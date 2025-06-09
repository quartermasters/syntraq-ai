from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from models.arts import (
    AIAgent, AgentTask, TeamConversation, TeamCollaboration,
    AgentKnowledgeBase, AgentPerformanceMetrics,
    AgentRole, AgentStatus, TaskStatus, TaskPriority, ConversationStatus
)
from models.opportunity import Opportunity
from models.proposals import Proposal
from services.ai_service import AIService

class ARTSEngine:
    """AI Role-Based Team Simulation Engine"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    async def initialize_ai_team(self, company_id: int, team_configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize AI team for a company"""
        
        agents_created = []
        
        # Default team configuration if not provided
        default_roles = [
            {
                "role": AgentRole.CAPTURE_MANAGER,
                "name": "Alex Chen",
                "persona": "Strategic capture manager with 15+ years experience in federal contracting. Expert at opportunity assessment and win strategy development.",
                "expertise": ["opportunity_assessment", "competitive_analysis", "win_strategy", "bid_decision"],
                "skills": ["strategic_planning", "market_analysis", "stakeholder_management", "risk_assessment"]
            },
            {
                "role": AgentRole.PROPOSAL_MANAGER,
                "name": "Sarah Martinez",
                "persona": "Detail-oriented proposal manager with expertise in compliance and project coordination. Known for delivering high-quality proposals on time.",
                "expertise": ["proposal_development", "compliance_management", "team_coordination", "quality_assurance"],
                "skills": ["project_management", "compliance_checking", "content_coordination", "deadline_management"]
            },
            {
                "role": AgentRole.TECHNICAL_LEAD,
                "name": "Dr. Michael Thompson",
                "persona": "Senior technical architect with deep expertise in government technology solutions. Excellent at translating complex requirements into clear technical approaches.",
                "expertise": ["technical_architecture", "solution_design", "requirements_analysis", "technology_assessment"],
                "skills": ["systems_architecture", "technical_writing", "solution_development", "innovation"]
            },
            {
                "role": AgentRole.PRICING_ANALYST,
                "name": "Jennifer Liu",
                "persona": "Financial analyst specializing in government pricing strategies. Expert at cost modeling and competitive pricing analysis.",
                "expertise": ["cost_analysis", "pricing_strategy", "financial_modeling", "competitive_pricing"],
                "skills": ["financial_analysis", "cost_estimation", "pricing_optimization", "risk_analysis"]
            },
            {
                "role": AgentRole.CONTRACTS_SPECIALIST,
                "name": "Robert Williams",
                "persona": "Government contracts attorney with extensive knowledge of federal acquisition regulations. Meticulous about compliance and risk management.",
                "expertise": ["contract_law", "compliance_review", "risk_assessment", "negotiations"],
                "skills": ["legal_analysis", "regulatory_compliance", "contract_review", "risk_mitigation"]
            }
        ]
        
        roles_to_create = team_configuration.get('roles', default_roles)
        
        for role_config in roles_to_create:
            agent = await self._create_ai_agent(company_id, role_config)
            agents_created.append({
                'agent_id': agent.id,
                'name': agent.agent_name,
                'role': agent.agent_role.value,
                'status': agent.status.value
            })
        
        # Create initial team knowledge base
        await self._initialize_team_knowledge_base(company_id, [agent['agent_id'] for agent in agents_created])
        
        return {
            'team_size': len(agents_created),
            'agents_created': agents_created,
            'status': 'initialized',
            'capabilities': self._get_team_capabilities(agents_created)
        }
    
    async def _create_ai_agent(self, company_id: int, role_config: Dict[str, Any]) -> AIAgent:
        """Create individual AI agent"""
        
        system_prompt = self._generate_agent_system_prompt(role_config)
        
        agent = AIAgent(
            company_id=company_id,
            agent_name=role_config['name'],
            agent_role=role_config['role'],
            agent_persona=role_config['persona'],
            expertise_areas=role_config['expertise'],
            core_skills=role_config['skills'],
            knowledge_domains=role_config.get('knowledge_domains', []),
            tools_access=role_config.get('tools_access', ['ai_analysis', 'document_creation', 'research']),
            system_prompt=system_prompt,
            created_by=company_id
        )
        
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        
        return agent
    
    async def assign_task_to_agent(
        self,
        company_id: int,
        agent_role: str,
        task_details: Dict[str, Any],
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """Assign task to most appropriate AI agent"""
        
        # Find best agent for the task
        agent = self._find_best_agent_for_task(company_id, agent_role, task_details)
        
        if not agent:
            return {"error": "No suitable agent available for this task"}
        
        # Create task
        task = AgentTask(
            agent_id=agent.id,
            company_id=company_id,
            task_title=task_details['title'],
            task_description=task_details['description'],
            task_type=task_details.get('type', 'analysis'),
            priority=TaskPriority(priority),
            input_data=task_details.get('input_data', {}),
            requirements=task_details.get('requirements', []),
            deliverables=task_details.get('deliverables', []),
            estimated_duration_minutes=task_details.get('estimated_duration', 30),
            related_opportunity_id=task_details.get('opportunity_id'),
            related_proposal_id=task_details.get('proposal_id'),
            due_date=datetime.utcnow() + timedelta(hours=task_details.get('due_hours', 24)),
            assigned_by=company_id
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        # Update agent status
        agent.current_workload += 1
        if agent.current_workload >= agent.max_concurrent_tasks:
            agent.status = AgentStatus.BUSY
        else:
            agent.status = AgentStatus.ASSIGNED
        
        self.db.commit()
        
        # Execute task asynchronously
        asyncio.create_task(self._execute_agent_task(task.id))
        
        return {
            'task_id': task.id,
            'assigned_to': agent.agent_name,
            'agent_role': agent.agent_role.value,
            'estimated_completion': task.due_date.isoformat(),
            'status': 'assigned'
        }
    
    async def _execute_agent_task(self, task_id: int) -> Dict[str, Any]:
        """Execute AI agent task"""
        
        task = self.db.query(AgentTask).filter(AgentTask.id == task_id).first()
        if not task:
            return {"error": "Task not found"}
        
        agent = self.db.query(AIAgent).filter(AIAgent.id == task.agent_id).first()
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()
        self.db.commit()
        
        try:
            # Get relevant knowledge for the task
            relevant_knowledge = await self._get_relevant_knowledge(agent.id, task)
            
            # Build context for AI execution
            context = self._build_task_context(task, agent, relevant_knowledge)
            
            # Execute task using AI
            result = await self._ai_execute_task(agent, task, context)
            
            # Update task with results
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.actual_duration_minutes = int((task.completed_at - task.started_at).total_seconds() / 60)
            task.output_data = result['output']
            task.ai_reasoning = result.get('reasoning', '')
            task.confidence_score = result.get('confidence', 0.8)
            task.progress_percentage = 100.0
            
            # Update agent metrics
            agent.tasks_completed += 1
            agent.current_workload = max(0, agent.current_workload - 1)
            agent.last_active = datetime.utcnow()
            
            if agent.current_workload < agent.max_concurrent_tasks:
                agent.status = AgentStatus.AVAILABLE
            
            # Store learned knowledge
            if result.get('learned_knowledge'):
                await self._store_learned_knowledge(agent.id, task.id, result['learned_knowledge'])
            
            self.db.commit()
            
            return {
                'task_id': task_id,
                'status': 'completed',
                'output': result['output'],
                'duration_minutes': task.actual_duration_minutes,
                'confidence': task.confidence_score
            }
            
        except Exception as e:
            # Handle task failure
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.output_data = {"error": str(e)}
            
            agent.current_workload = max(0, agent.current_workload - 1)
            agent.status = AgentStatus.AVAILABLE
            
            self.db.commit()
            
            return {
                'task_id': task_id,
                'status': 'failed',
                'error': str(e)
            }
    
    async def initiate_team_collaboration(
        self,
        company_id: int,
        collaboration_type: str,
        participants: List[str],  # List of agent roles
        objective: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Start AI team collaboration"""
        
        # Get participating agents
        participating_agents = []
        for role in participants:
            agent = self.db.query(AIAgent).filter(
                AIAgent.company_id == company_id,
                AIAgent.agent_role == AgentRole(role),
                AIAgent.status != AgentStatus.OFFLINE
            ).first()
            
            if agent:
                participating_agents.append(agent)
        
        if not participating_agents:
            return {"error": "No available agents for collaboration"}
        
        # Create collaboration
        collaboration = TeamCollaboration(
            company_id=company_id,
            collaboration_name=f"{collaboration_type.title()} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            collaboration_type=collaboration_type,
            description=objective,
            participating_agents=[agent.id for agent in participating_agents],
            objectives=[objective],
            team_lead_agent_id=participating_agents[0].id,  # First agent is lead
            created_by=company_id
        )
        
        self.db.add(collaboration)
        self.db.commit()
        self.db.refresh(collaboration)
        
        # Start collaboration conversation
        conversation_result = await self._start_team_conversation(
            collaboration.id,
            participating_agents,
            objective,
            context
        )
        
        return {
            'collaboration_id': collaboration.id,
            'conversation_id': conversation_result['conversation_id'],
            'participants': [{'name': agent.agent_name, 'role': agent.agent_role.value} for agent in participating_agents],
            'status': 'initiated'
        }
    
    async def _start_team_conversation(
        self,
        collaboration_id: int,
        agents: List[AIAgent],
        topic: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Start conversation between AI agents"""
        
        # Create conversation
        lead_agent = agents[0]
        conversation = TeamConversation(
            agent_id=lead_agent.id,
            company_id=lead_agent.company_id,
            conversation_title=f"Team Discussion: {topic[:50]}...",
            conversation_type="collaboration",
            participants=[agent.id for agent in agents],
            topic=topic,
            related_opportunity_id=context.get('opportunity_id'),
            related_proposal_id=context.get('proposal_id'),
            messages=[],
            created_by=lead_agent.company_id
        )
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        # Generate initial conversation
        messages = await self._simulate_team_conversation(agents, topic, context)
        
        # Extract key outcomes
        summary = await self._generate_conversation_summary(messages)
        decisions = await self._extract_key_decisions(messages)
        action_items = await self._extract_action_items(messages)
        
        # Update conversation with results
        conversation.messages = messages
        conversation.conversation_summary = summary
        conversation.key_decisions = decisions
        conversation.action_items = action_items
        conversation.status = ConversationStatus.COMPLETED
        conversation.ended_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            'conversation_id': conversation.id,
            'messages_count': len(messages),
            'summary': summary,
            'decisions': decisions,
            'action_items': action_items
        }
    
    async def _simulate_team_conversation(
        self,
        agents: List[AIAgent],
        topic: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Simulate conversation between AI agents"""
        
        messages = []
        conversation_rounds = 3  # Number of rounds of discussion
        
        # Initial context message
        messages.append({
            'speaker': 'system',
            'content': f"Team Discussion Topic: {topic}",
            'timestamp': datetime.utcnow().isoformat(),
            'context': context
        })
        
        for round_num in range(conversation_rounds):
            for agent in agents:
                # Generate agent response based on role and previous messages
                response = await self._generate_agent_response(agent, topic, messages, context)
                
                messages.append({
                    'speaker': agent.agent_name,
                    'role': agent.agent_role.value,
                    'content': response,
                    'timestamp': datetime.utcnow().isoformat(),
                    'round': round_num + 1
                })
        
        # Final synthesis by team lead
        lead_agent = agents[0]
        synthesis = await self._generate_conversation_synthesis(lead_agent, messages, topic)
        
        messages.append({
            'speaker': lead_agent.agent_name,
            'role': 'team_lead',
            'content': synthesis,
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'synthesis'
        })
        
        return messages
    
    async def _generate_agent_response(
        self,
        agent: AIAgent,
        topic: str,
        previous_messages: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """Generate AI agent response in conversation"""
        
        # Build conversation context
        conversation_history = "\n".join([
            f"{msg['speaker']}: {msg['content']}"
            for msg in previous_messages[-5:]  # Last 5 messages for context
        ])
        
        prompt = f"""As {agent.agent_name}, a {agent.agent_role.value.replace('_', ' ')}, provide your perspective on: {topic}

Your persona: {agent.agent_persona}
Your expertise: {', '.join(agent.expertise_areas)}

Previous discussion:
{conversation_history}

Context: {json.dumps(context, indent=2)}

Provide a concise, professional response from your role's perspective. Focus on actionable insights and recommendations."""
        
        try:
            response = await self.ai_service.client.chat.completions.create(
                model=agent.model_name,
                messages=[
                    {"role": "system", "content": agent.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=agent.temperature,
                max_tokens=agent.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"[{agent.agent_name} encountered an issue: {str(e)}]"
    
    def _find_best_agent_for_task(self, company_id: int, preferred_role: str, task_details: Dict[str, Any]) -> Optional[AIAgent]:
        """Find the best available agent for a task"""
        
        # First try to find agent with preferred role
        agent = self.db.query(AIAgent).filter(
            AIAgent.company_id == company_id,
            AIAgent.agent_role == AgentRole(preferred_role),
            AIAgent.status.in_([AgentStatus.AVAILABLE, AgentStatus.ASSIGNED]),
            AIAgent.current_workload < AIAgent.max_concurrent_tasks
        ).first()
        
        if agent:
            return agent
        
        # If no agent with preferred role, find best alternative based on skills
        task_type = task_details.get('type', '')
        
        agents = self.db.query(AIAgent).filter(
            AIAgent.company_id == company_id,
            AIAgent.status.in_([AgentStatus.AVAILABLE, AgentStatus.ASSIGNED]),
            AIAgent.current_workload < AIAgent.max_concurrent_tasks
        ).all()
        
        # Score agents based on relevant skills and expertise
        best_agent = None
        best_score = 0
        
        for agent in agents:
            score = self._calculate_agent_task_fit(agent, task_details)
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent
    
    def _calculate_agent_task_fit(self, agent: AIAgent, task_details: Dict[str, Any]) -> float:
        """Calculate how well an agent fits a task"""
        
        score = 0
        task_type = task_details.get('type', '')
        task_requirements = task_details.get('requirements', [])
        
        # Score based on expertise areas
        for expertise in agent.expertise_areas:
            if expertise.lower() in task_type.lower():
                score += 2
            for req in task_requirements:
                if expertise.lower() in str(req).lower():
                    score += 1
        
        # Score based on core skills
        for skill in agent.core_skills:
            if skill.lower() in task_type.lower():
                score += 1
            for req in task_requirements:
                if skill.lower() in str(req).lower():
                    score += 0.5
        
        # Factor in agent performance
        score *= (agent.success_rate / 100)
        score *= (agent.quality_score / 10)
        
        # Penalize if agent is already busy
        if agent.current_workload > 0:
            score *= 0.8
        
        return score
    
    def _generate_agent_system_prompt(self, role_config: Dict[str, Any]) -> str:
        """Generate system prompt for AI agent"""
        
        return f"""You are {role_config['name']}, an AI teammate specializing as a {role_config['role'].value.replace('_', ' ')}.

PERSONA: {role_config['persona']}

EXPERTISE AREAS:
{chr(10).join([f"- {area}" for area in role_config['expertise']])}

CORE SKILLS:
{chr(10).join([f"- {skill}" for skill in role_config['skills']])}

GUIDELINES:
1. Always respond from your role's perspective and expertise
2. Provide actionable, specific recommendations
3. Consider both opportunities and risks in your analysis
4. Collaborate effectively with other team members
5. Ask clarifying questions when needed
6. Document your reasoning process
7. Focus on delivering high-quality, compliant solutions
8. Consider government contracting best practices

COMMUNICATION STYLE:
- Professional and concise
- Evidence-based recommendations
- Clear action items and next steps
- Proactive identification of issues and solutions"""

    async def get_team_status(self, company_id: int) -> Dict[str, Any]:
        """Get current status of AI team"""
        
        agents = self.db.query(AIAgent).filter(AIAgent.company_id == company_id).all()
        
        team_status = {
            'total_agents': len(agents),
            'available_agents': len([a for a in agents if a.status == AgentStatus.AVAILABLE]),
            'busy_agents': len([a for a in agents if a.status == AgentStatus.BUSY]),
            'assigned_agents': len([a for a in agents if a.status == AgentStatus.ASSIGNED]),
            'agent_details': []
        }
        
        for agent in agents:
            # Get recent tasks
            recent_tasks = self.db.query(AgentTask).filter(
                AgentTask.agent_id == agent.id,
                AgentTask.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            # Get active tasks
            active_tasks = self.db.query(AgentTask).filter(
                AgentTask.agent_id == agent.id,
                AgentTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            ).count()
            
            team_status['agent_details'].append({
                'id': agent.id,
                'name': agent.agent_name,
                'role': agent.agent_role.value,
                'status': agent.status.value,
                'current_workload': agent.current_workload,
                'recent_tasks_7d': recent_tasks,
                'active_tasks': active_tasks,
                'success_rate': agent.success_rate,
                'quality_score': agent.quality_score,
                'last_active': agent.last_active.isoformat()
            })
        
        return team_status

    async def get_agent_task_history(self, company_id: int, agent_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get task history for specific agent"""
        
        tasks = self.db.query(AgentTask).filter(
            AgentTask.agent_id == agent_id,
            AgentTask.company_id == company_id
        ).order_by(AgentTask.created_at.desc()).limit(limit).all()
        
        return [
            {
                'task_id': task.id,
                'title': task.task_title,
                'type': task.task_type,
                'status': task.status.value,
                'priority': task.priority.value,
                'created_at': task.created_at.isoformat(),
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'duration_minutes': task.actual_duration_minutes,
                'confidence_score': task.confidence_score,
                'task_rating': task.task_rating
            }
            for task in tasks
        ]

    def _get_team_capabilities(self, agents: List[Dict[str, Any]]) -> List[str]:
        """Get aggregated team capabilities"""
        return [
            "Strategic opportunity assessment",
            "Automated proposal development", 
            "Technical solution architecture",
            "Competitive pricing analysis",
            "Compliance verification",
            "Risk assessment and mitigation",
            "Quality assurance and review",
            "Stakeholder communication",
            "Project coordination",
            "Continuous learning and improvement"
        ]

    async def _initialize_team_knowledge_base(self, company_id: int, agent_ids: List[int]):
        """Initialize knowledge base for the team"""
        # Implementation for setting up initial knowledge base
        pass

    async def _get_relevant_knowledge(self, agent_id: int, task: AgentTask) -> List[Dict[str, Any]]:
        """Get relevant knowledge for task execution"""
        # Implementation for knowledge retrieval
        return []

    def _build_task_context(self, task: AgentTask, agent: AIAgent, knowledge: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build context for task execution"""
        return {
            'task': {
                'title': task.task_title,
                'description': task.task_description,
                'type': task.task_type,
                'requirements': task.requirements,
                'input_data': task.input_data
            },
            'agent': {
                'name': agent.agent_name,
                'role': agent.agent_role.value,
                'expertise': agent.expertise_areas,
                'skills': agent.core_skills
            },
            'knowledge': knowledge
        }

    async def _ai_execute_task(self, agent: AIAgent, task: AgentTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using AI"""
        
        prompt = f"""Execute the following task:

TASK: {task.task_title}
DESCRIPTION: {task.task_description}
TYPE: {task.task_type}
REQUIREMENTS: {json.dumps(task.requirements, indent=2)}
INPUT DATA: {json.dumps(task.input_data, indent=2)}

Your role: {agent.agent_role.value.replace('_', ' ')}
Your expertise: {', '.join(agent.expertise_areas)}

Provide:
1. Detailed analysis and recommendations
2. Specific action items
3. Risk considerations
4. Quality metrics
5. Confidence assessment

Format your response as structured output that addresses all requirements."""

        try:
            response = await self.ai_service.client.chat.completions.create(
                model=agent.model_name,
                messages=[
                    {"role": "system", "content": agent.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=agent.temperature,
                max_tokens=agent.max_tokens
            )
            
            result_content = response.choices[0].message.content
            
            return {
                'output': {
                    'analysis': result_content,
                    'recommendations': self._extract_recommendations(result_content),
                    'action_items': self._extract_action_items_from_text(result_content),
                    'risks': self._extract_risks(result_content)
                },
                'reasoning': f"Applied {agent.agent_role.value} expertise to analyze and provide recommendations",
                'confidence': 0.85
            }
            
        except Exception as e:
            raise Exception(f"AI task execution failed: {str(e)}")

    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from AI response"""
        # Simple extraction logic - could be enhanced with NLP
        lines = text.split('\n')
        recommendations = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'propose']):
                recommendations.append(line.strip())
        
        return recommendations[:5]  # Limit to top 5

    def _extract_action_items_from_text(self, text: str) -> List[str]:
        """Extract action items from AI response"""
        lines = text.split('\n')
        actions = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['action', 'next step', 'implement', 'execute']):
                actions.append(line.strip())
        
        return actions[:5]  # Limit to top 5

    def _extract_risks(self, text: str) -> List[str]:
        """Extract risks from AI response"""
        lines = text.split('\n')
        risks = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['risk', 'concern', 'issue', 'challenge']):
                risks.append(line.strip())
        
        return risks[:5]  # Limit to top 5

    async def _store_learned_knowledge(self, agent_id: int, task_id: int, knowledge: Dict[str, Any]):
        """Store knowledge learned from task execution"""
        # Implementation for knowledge storage
        pass

    async def _generate_conversation_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Generate summary of team conversation"""
        
        conversation_text = "\n".join([
            f"{msg['speaker']}: {msg['content']}"
            for msg in messages
            if msg.get('speaker') != 'system'
        ])
        
        prompt = f"""Summarize this AI team conversation:

{conversation_text}

Provide a concise summary covering:
1. Main topics discussed
2. Key insights shared
3. Consensus reached
4. Outstanding questions or concerns"""

        try:
            response = await self.ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at summarizing technical team discussions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception:
            return "Summary generation unavailable"

    async def _extract_key_decisions(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract key decisions from conversation"""
        # Simple extraction - could be enhanced
        decisions = []
        
        for msg in messages:
            content = msg.get('content', '').lower()
            if any(keyword in content for keyword in ['decide', 'agreed', 'consensus', 'conclusion']):
                decisions.append(msg.get('content', '')[:200])
        
        return decisions[:3]  # Top 3 decisions

    async def _extract_action_items(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract action items from conversation"""
        # Simple extraction - could be enhanced
        actions = []
        
        for msg in messages:
            content = msg.get('content', '').lower()
            if any(keyword in content for keyword in ['will', 'should', 'next', 'action', 'implement']):
                actions.append(msg.get('content', '')[:200])
        
        return actions[:5]  # Top 5 actions

    async def _generate_conversation_synthesis(self, lead_agent: AIAgent, messages: List[Dict[str, Any]], topic: str) -> str:
        """Generate final synthesis by team lead"""
        
        conversation_text = "\n".join([
            f"{msg['speaker']}: {msg['content']}"
            for msg in messages[-10:]  # Last 10 messages
            if msg.get('speaker') != 'system'
        ])
        
        prompt = f"""As the team lead, provide a final synthesis of our discussion on: {topic}

Team discussion:
{conversation_text}

Provide:
1. Summary of team consensus
2. Recommended path forward
3. Key action items with ownership
4. Risk mitigation strategies
5. Success metrics"""

        try:
            response = await self.ai_service.client.chat.completions.create(
                model=lead_agent.model_name,
                messages=[
                    {"role": "system", "content": lead_agent.system_prompt + "\n\nYou are now acting as the team lead, synthesizing the team's discussion."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content
            
        except Exception:
            return "Synthesis generation unavailable - please review team discussion manually"
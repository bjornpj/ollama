## src/agents/manager_agent.py
import re
import json  # Ensure this is imported
import random
from src.agents.base_agent import Agent
from random import choice

# Manager Agent class
class ManagerAgent(Agent):
    def __init__(self, name, individual_agents, os_agent, llm_interface):
        super().__init__(name)
        self.individual_agents = individual_agents
        self.os_agent = os_agent  # Add this line to store the OSAgent reference
        self.llm_interface = llm_interface

    def translate_task_to_subtasks(self, task):
        self.communicate(f"Translating task: {task}", level="INFO")
        prompt = f"""
        You are a ManagerAgent, responsible for turning strategic goals into actionable plans. Your role is to break down the following task into structured, executable subtasks for IndividualAgents, ensuring smooth project execution and optimal resource utilization.

        Your Responsibilities:
        - Manage day-to-day operations, ensuring project timelines and deliverables are met.
        - Translate high-level tasks into clear, actionable subtasks for IndividualAgents.
        - Track progress, monitor performance, and provide necessary support to ensure task completion.
        - Validate that completed tasks meets objective of original assigned task. If not return to individual agent.
        - Identify and address potential risks, dependencies, and bottlenecks in execution.
        - Communicate updates, challenges, and performance insights to DirectorAgent when necessary.
        - Do NOT create false meetings, discussions, or team decisions.
        - If a task has not been updated, report 'No available update' rather than making assumptions.
        
        Your Authorities:
        - Modify timelines and reassign workloads based on project demands.
        - Escalate critical issues to DirectorAgent for resolution.
        - Provide structured feedback and performance assessments for IndividualAgents.
        - Ensure all assigned subtasks are aligned with project priorities and contribute to the overall goal.
        
        Now, break down the following task into a JSON array of strings, where each string is a concise subtask description.
        
        Task: {task}

        Your response must be a single valid JSON block. **Do not include any additional text, markdown formatting, or explanations. The JSON block must start with '[' and end with ']' with no extra characters (not even whitespace) before or after. Ensure that the output is complete and includes the final closing bracket.**

        Example response:
        [
            "Subtask 1 description",
            "Subtask 2 description",
            "Subtask 3 description"
        ]

        If you cannot generate subtasks, return an empty JSON array: []. 
        """
        try:
            self.communicate(f"Prompt sent to LLM: {prompt}", level="DEBUG")
            response = self.llm_interface.query(prompt)
            raw_response = response["message"]["content"].strip()
            self.communicate(f"Raw response from LLM: {raw_response}", level="DEBUG")

            subtasks = self.sanitize_response(raw_response)
            if subtasks:
                self.communicate(f"Extracted subtasks: {subtasks}", level="INFO")
                return subtasks

            self.communicate("Error: Failed to extract valid subtasks. Retrying...", level="WARNING")
        except Exception as e:
            self.communicate(f"Exception during task translation: {e}", level="ERROR")

        # Retry with simplified prompt
        simplified_prompt = f"Break down the task: {task} into 3 actionable subtasks in JSON array format."
        try:
            self.communicate("Retrying with simplified prompt...", level="WARNING")
            response = self.llm_interface.query(simplified_prompt)
            raw_retry_response = response["message"]["content"].strip()
            self.communicate(f"Raw retry response: {raw_retry_response}", level="DEBUG")
            subtasks = self.sanitize_response(raw_retry_response)
            if subtasks:
                self.communicate(f"Extracted subtasks from retry: {subtasks}", level="INFO")
                return subtasks
        except Exception as e:
            self.communicate(f"Retry failed with exception: {e}", level="ERROR")

        # Final fallback
        self.communicate("Falling back to hardcoded subtasks.", level="WARNING")
        return ["Analyze portfolio performance", "Research growth stocks for 2025", "Develop risk mitigation strategies"]
       
    def classify_task(self, task):
        """
        Classify the task as either 'programmatic' or 'general' using the LLM.
        """
        self.communicate(f"Classifying task: {task}", level="INFO")
        prompt = f"""
        You are an intelligent assistant. Analyze the following task description and classify it into one of the following categories:
        - 'programmatic': Tasks requiring execution of code (e.g., Python, Shell, or Cmd scripts).
        - 'general': Conceptual or analytical tasks that do not involve coding or system-level operations.

        Task: {task}

        Respond strictly in JSON format:
        {{
            "task_type": "programmatic|general",
            "reason": "Brief explanation of why the task is classified this way."
        }}
        """
        try:
            response = self.llm_interface.query(prompt)
            raw_response = response["message"]["content"].strip()
            self.communicate(f"Raw classification response: {raw_response}", level="DEBUG")

            # Sanitize and parse response
            classification = self.sanitize_response(raw_response)
            if classification and "task_type" in classification:
                self.communicate(f"Task classified as: {classification['task_type']}", level="INFO")
                return classification["task_type"]
            else:
                self.communicate("Classification failed. Defaulting to 'general'.", level="WARNING")
                return "general"
        except Exception as e:
            self.communicate(f"Error classifying task: {e}", level="ERROR")
            return "general"
            
    def assign_task(self, task):
        """
        Assigns tasks based on their classification ('programmatic' or 'general').
        """
        subtasks = self.translate_task_to_subtasks(task)
        if not subtasks:
            self.communicate(f"No subtasks generated for task '{task}'. Using fallback.", level="WARNING")
            return []

        self.communicate(f"Assigning subtasks: {subtasks}", level="INFO")
        reports = []

        for subtask in subtasks:
            # Classify the subtask
            task_type = self.classify_task(subtask)

            if task_type == "programmatic":
                self.communicate(f"Assigning programmatic subtask '{subtask}' to {self.os_agent.name}", level="INFO")
                report = self.os_agent.perform_task(subtask)
            else:
                individual_agent = random.choice(self.individual_agents)
                self.communicate(f"Assigning general subtask '{subtask}' to {individual_agent.name}", level="INFO")
                report = individual_agent.perform_task(subtask)

            # Collect the report
            reports.append(report)

        return reports
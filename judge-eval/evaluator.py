from models import Prompt, Metric, ModelInfo
from deepeval.test_case import LLMTestCase
from metric_creator import MetricCreator
from llmrequestor import LlmRequestor
from eval_logger import EvalLogger
import json

class Evaluator:
    def __init__(self, prompt: Prompt, metric: Metric, model: ModelInfo, system_prompt: str = ""):
        self.prompt = prompt
        self.metric = metric
        self.model = model
        self.system_prompt = system_prompt

        # one logger instance per evaluation.
        self.eval_logger = EvalLogger(enable_terminal_output=True, verbose_terminal=True)
        self.eval_logger.info("evaluator", "Initialized evaluator", {
            "prompt_input": prompt.input[:100] + "..." if len(prompt.input) > 100 else prompt.input,
            "metric_name": metric.name,
            "metric_type": metric.type,
            "model_name": model.name,
            "has_system_prompt": bool(system_prompt)
        })

    def evaluate(self):
        self.eval_logger.info("evaluator", "Starting evaluation process")

        if self.metric.type == "tool-use":
            # The tool-use metric loop produces actual_output itself (full conversation
            # including tool rounds), so the single-request model call is skipped.
            self.eval_logger.info("evaluator", "Tool-use metric: skipping direct model request (loop builds output)")

            metric_creator = MetricCreator(self.metric, model=self.model, system_prompt=self.system_prompt, logger=self.eval_logger)
            metric_instance = metric_creator.create_metric()

            context_list = [self.prompt.context] if self.prompt.context else []
            test_case = LLMTestCase(
                input=self.prompt.input,
                actual_output="",  # wird vom Metrik-Loop erzeugt
                expected_output=self.prompt.expected_output,
                context=context_list
            )

            self.eval_logger.info("evaluator", "Starting metric measurement for tool-use")
            metric_instance.measure(test_case)

            self.eval_logger.info("evaluator", "Evaluation completed", {
                "score": metric_instance.score,
                "reason_length": len(metric_instance.reason) if metric_instance.reason else 0
            })

            # The metric loop's final answer is the model's actual response:
            actual_output = getattr(metric_instance, "final_answer", "") or "(no final answer: aborted or round limit reached)"

            logs = self.eval_logger.get_logs()
            # Tool-round transcript as structured extra info for the UI:
            rounds_info = getattr(metric_instance, "rounds", [])
            end_reason = getattr(metric_instance, "end_reason", "")
            logs = logs + [
                {"timestamp": "", "level": "SUMMARY", "component": "tool_use_metric",
                 "message": f"END: {end_reason}", "data": {"rounds": rounds_info}}
            ]

            result = {
                'actual_output': actual_output,
                'score': metric_instance.score,
                'reason': metric_instance.reason,
                'logs': json.dumps(logs)
            }
            return result

        # Generate actual output using the model
        self.eval_logger.info("evaluator", "Requesting LLM response for evaluation")
        requestor = LlmRequestor(self.prompt, self.model, self.system_prompt, logger=self.eval_logger)
        actual_output = requestor.request()

        self.eval_logger.info("evaluator", "Creating test case", {
            "has_expected_output": bool(self.prompt.expected_output),
            "has_context": bool(self.prompt.context),
            "actual_output_length": len(actual_output)
        })

        # Create test case with actual output
        context_list = [self.prompt.context] if self.prompt.context else [] #context is usually one string from eval gui
        test_case = LLMTestCase(
            input=self.prompt.input,
            actual_output=actual_output,
            expected_output=self.prompt.expected_output,
            context=context_list
        )

        # Create metric instance and evaluate
        self.eval_logger.info("evaluator", "Creating metric instance")
        metric_instance = MetricCreator(self.metric, logger=self.eval_logger).create_metric()
        
        self.eval_logger.info("evaluator", "Starting metric measurement")
        # Measure the test case
        metric_instance.measure(test_case)
        
        self.eval_logger.info("evaluator", "Evaluation completed", {
            "score": metric_instance.score,
            "reason_length": len(metric_instance.reason) if metric_instance.reason else 0
        })
        
        result = {
            'actual_output': actual_output,
            'score': metric_instance.score,
            'reason': metric_instance.reason,
            'logs': json.dumps(self.eval_logger.get_logs())  # Convert logs array to JSON string
        }
        
        self.eval_logger.info("evaluator", "Returning evaluation result with logs", {
            "total_log_entries": len(self.eval_logger.get_logs())
        })
        
        return result
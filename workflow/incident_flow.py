from agents.anomaly_agent import AnomalyAgent
from agents.rca_agent import RCAAgent
from agents.remediation_agent import RemediationAgent


class IncidentWorkflow:


    def __init__(self):

        self.anomaly_agent = AnomalyAgent()
        self.rca_agent = RCAAgent()
        self.remediation_agent = RemediationAgent()



    def run(self, df):

        anomaly_result = (
            self.anomaly_agent
            .analyze(df)
        )


        rca_result = (
            self.rca_agent
            .analyze(anomaly_result)
        )


        remediation = (
            self.remediation_agent
            .generate(rca_result)
        )


        return {

            "anomaly": anomaly_result,

            "rca": rca_result,

            "remediation": remediation

        }
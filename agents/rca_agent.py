class RCAAgent:

    def analyze(self, anomaly_result):

        anomalies = anomaly_result["anomalies"]


        if not anomalies:
            return {
                "root_cause":
                "No incident detected"
            }


        text = " ".join(anomalies).lower()


        if "timeout" in text:

            cause = (
                "Repeated timeout errors indicate "
                "possible dependency or network failure."
            )


        elif "connection" in text:

            cause = (
                "Connection failures indicate "
                "service communication problems."
            )


        elif "exception" in text:

            cause = (
                "Application exceptions indicate "
                "runtime failures."
            )


        else:

            cause = (
                "Application instability detected "
                "due to repeated error patterns."
            )


        return {
            "root_cause": cause
        }
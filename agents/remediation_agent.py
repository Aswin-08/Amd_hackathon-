class RemediationAgent:


    def generate(self, rca):

        cause = rca["root_cause"]


        actions = []


        if "network" in cause.lower():

            actions += [
                "Check dependent services",
                "Validate network connectivity"
            ]


        if "exception" in cause.lower():

            actions += [
                "Review application logs",
                "Restart unhealthy service"
            ]


        if "connectivity" in cause.lower():

            actions += [
                "Check database/service connection",
                "Restart connection pool"
            ]


        if not actions:

            actions.append(
                "Investigate application health"
            )


        return {
            "actions": actions
        }
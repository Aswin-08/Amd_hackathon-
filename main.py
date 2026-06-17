from workflow.incident_flow import IncidentWorkflow



def run_agent(df):

    workflow = IncidentWorkflow()

    result = workflow.run(df)

    return result
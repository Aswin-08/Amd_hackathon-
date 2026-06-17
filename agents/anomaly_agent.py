class AnomalyAgent:

    def analyze(self, df):

        print(df.columns)

        result = {
            "anomalies": [],
            "summary": {}
        }


        # normalize columns
        df.columns = [
            c.strip()
            for c in df.columns
        ]


        # basic summary

        result["summary"] = {
            "total_logs": len(df),
            "applications":
                df["app_name"].unique().tolist()
        }


        # error frequency

        errors = (
            df["error_code"]
            .value_counts()
            .to_dict()
        )


        for code, count in errors.items():

            # ignore successful codes
            if str(code) not in ["0", "200"]:

                result["anomalies"].append(
                    f"Error {code} occurred {count} times"
                )


        # keyword detection

        keywords = [
            "fail",
            "error",
            "timeout",
            "exception",
            "crash",
            "unavailable",
            "refused"
        ]


        for keyword in keywords:

            matches = df[
                df["message"]
                .astype(str)
                .str.contains(
                    keyword,
                    case=False
                )
            ]


            if len(matches) > 0:

                result["anomalies"].append(
                    f"Detected '{keyword}' pattern in logs"
                )


        return result
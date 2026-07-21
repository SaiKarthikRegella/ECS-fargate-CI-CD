from locust import HttpUser, task, between

class FlaskApiUser(HttpUser):
    wait_time = between(1, 1)  # mimics k6's sleep(1)
    host = "http://fld-1952811936.us-east-2.elb.amazonaws.com"

    @task
    def health_check(self):
        self.client.get("/health")
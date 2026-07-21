from locust import HttpUser, TaskSet, task, between, constant
import sys
sys.path.append('../../')
import helpers.dateutils as dateutils
from datetime import datetime


class UserBehavior(TaskSet):
    basic_auth_user = "citywalk"
    basic_auth_pass = "klawytic"

    user_id = "pokipoki"
    facility_id = "fugafuga"
    get_facility_id = "hogehoge"
    lat = 32.7501286
    lon = 129.8674725
    timestamp = "2021-01-31'T'16:25:08.309648%2B0900"
    comment = "test comment"
    rate = 4

    @task(1)
    def api_history_location_gps(self):
        self.timestamp = str(dateutils.datetime_to_iso8061(datetime.now())).replace("+", "%2B")
        self.client.post(f"/v1/history/location/gps?userId={self.user_id}&facilityId={self.facility_id}&lat={self.lat}&lon={self.lon}&timestamp={self.timestamp}", verify=False, auth=(self.basic_auth_user, self.basic_auth_pass))

    @task(1)
    def api_submit_rating_facility(self):
        self.timestamp = str(dateutils.datetime_to_iso8061(datetime.now())).replace("+", "%2B")
        self.client.post(f"/v1/rating/facility/submit?userId={self.user_id}&facilityId={self.facility_id}&rate={self.rate}&comment={self.comment}&timestamp={self.timestamp}", verify=False, auth=(self.basic_auth_user, self.basic_auth_pass))

    @task(1)
    def api_get_rating_facility(self):
        self.client.get(f"/v1/rating/facility/{self.get_facility_id}/get", verify=False, auth=(self.basic_auth_user, self.basic_auth_pass))

class WebsiteUser(HttpUser):
    tasks = {UserBehavior:1}
    wait_time = constant(0)

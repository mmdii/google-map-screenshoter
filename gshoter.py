import requests


def map_screen_shooter(latitude, longitude):
    base_url = "https://maps.googleapis.com/maps/api/staticmap?"
    api_key = ""
    try:
        get_photo = requests.get(base_url+"center="+str(latitude) +
                                 ","+str(longitude)+"&zoom=17&size=400x400&"+"key="+api_key)
        get_photo.raise_for_status()
        f = open('robtakarim.png ', 'wb')
        f.write(get_photo.content)
        f.close()
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)


map_screen_shooter(35.475235, 51.0790807)


class GoogleMapScreenShooter:

    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def simple_screen_shoot(self):
        base_url = "https://maps.googleapis.com/maps/api/staticmap?"
        api_key = ""
        try:
            get_photo = requests.get(base_url+"center="+str(self.latitude) +
                                     ","+str(self.longitude)+"&zoom=10&size=400x400&"+"key="+api_key)
            get_photo.raise_for_status()
            f = open('robtakarim.png ', 'wb')
            f.write(get_photo.content)
            f.close()
        except requests.exceptions.HTTPError as e:
            raise SystemExit(e)

    def screen_shoot_with_marker():
        pass


# nice = GoogleMapScreenShooter(35.475235, 51.0790807)
# nice.simple_screen_shoot()

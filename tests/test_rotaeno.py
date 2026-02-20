import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
import rotaeno

user_profiles = [
    {
        "serverCode": "cn",
        "objectID": "",
        "sessionToken": ""
    },
    {
        "serverCode": "global",
        "objectID": "",
        "sessionToken": ""
    },
    {
        "serverCode": "friend_cn",
        "shortID": ""
    },
    {
        "serverCode": "friend_global",
        "shortID": ""
    }
]

class TestRequestProcessor:
    @pytest.mark.skip(reason="COMPLEX")
    @pytest.mark.parametrize("user_profile", user_profiles)
    def test_get_cloud_save(self, user_profile):
        processor = rotaeno.api.processor.Processor(region=rotaeno.api.model.ServerRegion(user_profile["serverCode"]), user_profile=user_profile)
        cloud_save = processor.get_cloud_save()
        assert "songDatas" in cloud_save
    
    @pytest.mark.skip(reason="COMPLEX")
    @pytest.mark.parametrize("user_profile", user_profiles)
    def test_get_user_data(self, user_profile):
        processor = rotaeno.api.processor.Processor(region=rotaeno.api.model.ServerRegion(user_profile["serverCode"]), user_profile=user_profile)
        user_data = processor.get_user_data()
        assert "playerRating" in user_data
    
    @pytest.mark.skip(reason="COMPLEX")
    @pytest.mark.parametrize("user_profile", user_profiles)
    def test_get_followee_data(self, user_profile):
        processor = rotaeno.api.processor.Processor(region=rotaeno.api.model.ServerRegion(user_profile["serverCode"]), user_profile=user_profile)
        followee_data = processor.get_followee_data()
        assert isinstance(followee_data, list)

class TestProcessor:
    @pytest.mark.skip(reason="COMPLEX")
    @pytest.mark.parametrize("user_profile", user_profiles)
    def test_get_best40_data(self, user_profile):
        best40 = rotaeno.processor.get_best40(user_profile=user_profile, just_data=True)
        assert isinstance(best40, list)
    
    @pytest.mark.skip(reason="COMPLEX")
    @pytest.mark.parametrize("user_profile", user_profiles)
    def test_get_best40_image(self, user_profile):
        best40 = rotaeno.processor.get_best40(user_profile=user_profile)
        assert isinstance(best40, str)
    
    @pytest.mark.skip(reason="COMPLEX")
    @pytest.mark.parametrize("user_profile", user_profiles)
    def test_get_song_data(self, user_profile):
        song_id = "alive"
        song_data = rotaeno.processor.get_song(user_profile=user_profile, song_id=song_id, just_data=True)
        assert isinstance(song_data, dict)
    
    @pytest.mark.skip(reason="COMPLEX")
    @pytest.mark.parametrize("user_profile", user_profiles)
    def test_get_song_image(self, user_profile):
        song_id = "alive"
        song_image = rotaeno.processor.get_song(user_profile=user_profile, song_id=song_id)
        assert isinstance(song_image, str)
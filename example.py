import kalpa
import phigros
import rotaeno

kalpa.api.processor.MobileProcessor(
    client_version=30209,
    user_profile={
        "userid": "your_userid",
        "password": "your_password"
    }
).get_user_info()

phigros.processor.get_best30(
    user_profile={
        "serverCode": "cn",
        "sessionToken": "your_session_token"
    }, just_data=True
)

rotaeno.processor.get_best40(
    user_profile={
        "serverCode": "global",
        "objectID": "your_object_id",
        "sessionToken": "your_session_token",
        "locale": "en-US"
    }, just_data=True
)

rotaeno.processor.get_song(
    user_profile={
        "serverCode": "global",
        "objectID": "your_object_id",
        "sessionToken": "your_session_token"
    },
    song_id="song_id_here",
)

rotaeno.processor.get_song_status(
    user_profile={
        "serverCode": "global",
        "objectID": "your_object_id",
        "sessionToken": "your_session_token"
    },
    song_status="AP",
    just_html=True
)

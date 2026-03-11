def detect_ball(ball_model, frame):
    results = ball_model.predict(frame, verbose=False)
    return results[0]


def detect_person_pose(person_model, pose_model, frame):
    person_results = person_model.predict(frame, verbose=False)[0]
    pose_results = pose_model.predict(frame, verbose=False)[0]
    return person_results, pose_results

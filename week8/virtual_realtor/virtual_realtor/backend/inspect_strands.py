
try:
    from strands import Agent
    from strands.session.s3_session_manager import S3SessionManager
    print("Agent methods:", dir(Agent))
    print("S3SessionManager methods:", dir(S3SessionManager))
except ImportError as e:
    print("ImportError:", e)

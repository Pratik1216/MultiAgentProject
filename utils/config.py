from utils.packages import *
load_dotenv()

api_key = os.getenv("LITELLM_KEY")
client = OpenAI(api_key=api_key,
                base_url="http://3.110.18.218")
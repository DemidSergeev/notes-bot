import uuid
import uuid_utils

# Not really a facade. Will be removed after bumping Python to 3.14
def uuid7():
    return uuid.UUID(uuid_utils.uuid7().hex)
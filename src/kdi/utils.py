def get_priority_value(data: dict):
    for k, v in data.items():
        if "topic" in k.lower():
            return "topic", v
        if "comment" in k.lower():   
            return "comment", v
    return None, None
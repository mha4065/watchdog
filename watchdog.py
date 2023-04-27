import requests
import pymongo
from time import sleep
from discord_webhook import DiscordWebhook, DiscordEmbed


platforms = ['hackerone', 'bugcrowd', 'intigriti', 'yeswehack']

HACKERONE = "https://raw.githubusercontent.com/Osb0rn3/bugbounty-targets/4256468efce8d8aa9b3a0f00d3653fe50bae95ab/programs/hackerone.json"
BUGCROWD = "https://raw.githubusercontent.com/Osb0rn3/bugbounty-targets/main/programs/bugcrowd.json"
INTIGRITI = "https://raw.githubusercontent.com/Osb0rn3/bugbounty-targets/main/programs/intigriti.json"
YESWEHACK = "https://raw.githubusercontent.com/Osb0rn3/bugbounty-targets/main/programs/yeswehack.json"


def get_data(url:str):
    return requests.get(url).json()

def insert_db(data:dict, platform:str):
    # Connect to MongoDB client
    client = pymongo.MongoClient("mongodb://localhost:27017/")

    # Select database and collection
    db = client["bb_programs"]
    if platform in db.list_collection_names():
        print("Already exists!")
        return

    collection = db[platform]

    # Insert data into collection
    try:
        collection.insert_many(data)
        print("Successfully added to DB.")
        return True
    except Exception as e:
        print(e)


def check_changes(platform:str):
    # Connect to MongoDB client
    client = pymongo.MongoClient("mongodb://localhost:27017/")

    # Select database and collection
    db = client["bb_programs"]
    if platform == 'hackerone':
        collection = db["hackerone"]
        
        # get new data
        new_results = cleaner(get_data(HACKERONE), platform)
        for program in new_results:
            old_data = collection.find_one({"handle": program["handle"]})
            if old_data == None:
                collection.insert_one(program)
                continue
            for in_scope in program["in_scope"]:
                if in_scope not in old_data["in_scope"]:
                    collection.update_one({"handle": program["handle"]}, {"$push": {"in_scope": in_scope}})
                    push(program["logo"], program["name"], program["program_url"], platform, in_scope)
                    print(f"new scope found! {in_scope}")
            for out_of_scope in program["out_of_scope"]:
                if out_of_scope not in old_data["out_of_scope"]:
                    print(f"new out of scope found! {out_of_scope}")
                    collection.update_one({"handle": program["handle"]}, {"$push": {"out_of_scope": {out_of_scope}}})
    elif platform == 'bugcrowd':
        collection = db["bugcrowd"]
        # get new data
        new_results = cleaner(get_data(BUGCROWD), platform)
        for program in new_results:
            old_data = collection.find_one({"code": program["code"]})
            if old_data == None:
                collection.insert_one(program)
                continue
            for in_scope in program["in_scope"]:
                #print(in_scope)
                if in_scope not in old_data["in_scope"]:
                    collection.update_one({"code": program["code"]}, {"$push": {"in_scope": in_scope}})
                    push(program["logo"], program["name"], program["program_url"], platform, in_scope)
                    print(f"new scope found! {in_scope}")
            for out_of_scope in program["out_of_scope"]:
                if out_of_scope not in old_data["out_of_scope"]:
                    print(f"new out of scope found! {out_of_scope}")
                    collection.update_one({"code": program["code"]}, {"$push": {"out_of_scope": {out_of_scope}}})
    elif platform == 'intigriti':
        collection = db["intigriti"]
        # get new data
        new_results = cleaner(get_data(INTIGRITI), platform)
        for program in new_results:
            old_data = collection.find_one({"handle": program["handle"]})
            if old_data == None:
                collection.insert_one(program)
                continue
            for in_scope in program["in_scope"]:
                #print(in_scope)
                if in_scope not in old_data["in_scope"]:
                    collection.update_one({"handle": program["handle"]}, {"$push": {"in_scope": in_scope}})
                    push(program["logo"], program["name"], program["program_url"], platform, in_scope)
                    print(f"new scope found! {in_scope}")
            for out_of_scope in program["out_of_scope"]:
                if out_of_scope not in old_data["out_of_scope"]:
                    print(f"new out of scope found! {out_of_scope}")
                    collection.update_one({"handle": program["handle"]}, {"$push": {"out_of_scope": {out_of_scope}}})
    elif platform == 'yeswehack':
        collection = db["yeswehack"]
        # get new data
        new_results = cleaner(get_data(YESWEHACK), platform)
        for program in new_results:
            old_data = collection.find_one({"slug": program["slug"]})
            if old_data == None:
                collection.insert_one(program)
                continue
            for in_scope in program["in_scope"]:
                if in_scope not in old_data["in_scope"]:
                    collection.update_one({"slug": program["slug"]}, {"$push": {"in_scope": in_scope}})
                    push(program["logo"], program["title"], program["program_url"], platform, in_scope)
                    print(f"new scope found! {in_scope}")
            # for out_of_scope in program["out_of_scope"]:
            #     if out_of_scope not in old_data["out_of_scope"]:
            #         print(f"new out of scope found! {out_of_scope}")
            #         collection.update_one({"slug": program["slug"]}, {"$push": {"out_of_scope": {out_of_scope}}})
    else:
        pass
                

def cleaner(data:dict, platform:str):
    if platform == 'hackerone':
        programs = []
        for program in data:
            program_name = program["attributes"]["name"]
            program_handle = program["attributes"]["handle"]
            programScope = program["relationships"]["structured_scopes"]["data"]
            if len(programScope) == 0:
                continue
            programs_dict = {"name":program_name,
                             "handle": program_handle,
                             "program_url": "https://hackerone.com/" + program_handle,
                             "logo": program["attributes"]["profile_picture"],
                             "in_scope": [],
                             "out_of_scope": []}
            for x in programScope:
                if x["attributes"]["eligible_for_submission"]:
                    programs_dict["in_scope"].append(x["attributes"]["asset_identifier"])
                else:
                    programs_dict["out_of_scope"].append(x["attributes"]["asset_identifier"])
            programs.append(programs_dict)
        return programs
    elif platform == 'bugcrowd':
        programs = []
        for program in data:
            program_name = program["name"]
            program_code = program["code"]
            programScope = program["target_groups"]
            if len(programScope) == 0:
                continue
            programs_dict = {"name":program_name,
                             "code": program_code,
                             "program_url": "https://bugcrowd.com/" + program_code,
                             "logo": program["logo"],
                             "in_scope": [],
                             "out_of_scope": []}
            for x in programScope:
                if x["in_scope"] == True:
                    for y in x["targets"]:
                        programs_dict["in_scope"].append(y["uri"])
                else:
                    for y in x["targets"]:
                        programs_dict["out_of_scope"].append(y["name"])
            programs.append(programs_dict)
        return programs
    elif platform == 'intigriti':
        programs = []
        for program in data:
            program_name = program["name"]
            program_company_handle = program["companyHandle"]
            program_handle = program["handle"]
            programScope = program["domains"]
            if len(programScope) == 0:
                continue
            programs_dict = {"name":program_name,
                             "companyHandle": program_company_handle,
                             "handle": program_handle,
                             "program_url": "https://app.intigriti.com/programs/" + program_company_handle + "/" + program_handle,
                             "logo": "https://bff-public.intigriti.com/file/" + program["logoId"],
                             "in_scope": [],
                             "out_of_scope": []}
            for x in programScope:
                if x["description"] and 'Out of scope' in x["description"]:
                    programs_dict["out_of_scope"].append(x["endpoint"])
                else:
                    programs_dict["in_scope"].append(x["endpoint"])
            programs.append(programs_dict)
        return programs
    elif platform == 'yeswehack':
        programs = []
        for program in data:
            program_title = program["title"]
            program_slug = program["slug"]
            programScope = program["scopes"]
            if len(programScope) == 0:
                continue
            programs_dict = {"title":program_title,
                             "slug": program_slug,
                             "program_url": "https://yeswehack.com/programs/" + program_slug,
                             "logo": program["thumbnail"]["url"],
                             "in_scope": [],
                             "out_of_scope": []}
            for x in programScope:
                if x["scope_type"] == "web-application":
                    programs_dict["in_scope"].append(x["scope"])
                else:
                    # programs_dict["out_of_scope"].append(x["targets"]["name"])
                    pass
            programs.append(programs_dict)
        return programs
    else:
        return
    

def push(logo_url, program_name, program_url, platform, message:str):
    if platform == 'hackerone':
        webhook = DiscordWebhook(url="https://ptb.discord.com/api/webhooks/1100875059360436364/jFO75ZMDIaQXtERWLjSOoY2xLmxGoFXpbySYJ6aZDad_x282Wqn5R_ynDb2rai3yYgbu")
        embed = DiscordEmbed(title="HackerOne", description=message, color="ffffff")
        embed.set_thumbnail(url=logo_url)
        embed.add_embed_field(name="Program:", value=program_name)
        embed.add_embed_field(name="URL:", value=program_url)             
        webhook.add_embed(embed)
        response = webhook.execute()
    elif platform == 'bugcrowd':
        webhook = DiscordWebhook(url="https://ptb.discord.com/api/webhooks/1100875059360436364/jFO75ZMDIaQXtERWLjSOoY2xLmxGoFXpbySYJ6aZDad_x282Wqn5R_ynDb2rai3yYgbu")
        embed = DiscordEmbed(title="Bugcrowd", description=message, color="ff6900")
        embed.set_thumbnail(url=logo_url)
        embed.add_embed_field(name="Program:", value=program_name)
        embed.add_embed_field(name="URL:", value=program_url)             
        webhook.add_embed(embed)
        response = webhook.execute()
    elif platform == 'intigriti':
        webhook = DiscordWebhook(url="https://ptb.discord.com/api/webhooks/1100875059360436364/jFO75ZMDIaQXtERWLjSOoY2xLmxGoFXpbySYJ6aZDad_x282Wqn5R_ynDb2rai3yYgbu")
        embed = DiscordEmbed(title="Intigriti", description=message, color="4c59a8")
        embed.set_thumbnail(url=logo_url)
        embed.add_embed_field(name="Program:", value=program_name)
        embed.add_embed_field(name="URL:", value=program_url)             
        webhook.add_embed(embed)
        response = webhook.execute()
    elif platform == 'yeswehack':
        webhook = DiscordWebhook(url="https://ptb.discord.com/api/webhooks/1100875059360436364/jFO75ZMDIaQXtERWLjSOoY2xLmxGoFXpbySYJ6aZDad_x282Wqn5R_ynDb2rai3yYgbu")
        embed = DiscordEmbed(title="YesWeHack", description=message, color="8f0e0e")
        embed.set_thumbnail(url=logo_url)
        embed.add_embed_field(name="Program:", value=program_name)
        embed.add_embed_field(name="URL:", value=program_url)             
        webhook.add_embed(embed)
        response = webhook.execute()
    else:
        pass


def main():
    for platform in platforms:
        if platform == 'hackerone':
            result = get_data(HACKERONE)
        elif platform == 'bugcrowd':
            result = get_data(BUGCROWD)
        elif platform == 'intigriti':
            result = get_data(INTIGRITI)
        elif platform == 'yeswehack':
            result = get_data(YESWEHACK)
        else:
            return
        
        clean_result = cleaner(result, platform)
        insert_db(clean_result, platform)

    while True:
        sleep(5)
        for platform in platforms:
            check_changes(platform)


if __name__ == "__main__":
    main()
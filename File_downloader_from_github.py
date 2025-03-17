import requests
import os
from bs4 import BeautifulSoup

def Downloader(repo_link, base_path="/workspaces/SIMS-Project/Resume_Scrapper/Downloaded/code_files/"):
    file_name = repo_link.split("/")[-1]
    branch = "main"  # Change to "master" if needed

    # Step 1: Get all file paths
    response = requests.get(repo_link)
    soup = BeautifulSoup(response.text, 'html.parser')

    path = repo_link[repo_link.index(".com/") + 5:]
    
    links = soup.find_all('a', class_="Link--primary", href=True)
    links = [link['href'] for link in links]

    files = []
    for link in links:
        if "/blob/" in link:
            file_path = link.replace(f"{path}/blob/{branch}/", "")
            files.append(file_path)
        elif "/tree/" in link:
            Downloader("https://github.com" + link)
            
    files = list(set(files))
    # print(f"Found {len(files)} files in {repo_link}")
    files = [files[i][1:] for i in range(len(files))]
    # print(files)

    # Step 2: Download each file
    for file in files:
        raw_url = f"https://github.com/{path}/blob/{branch}/{file}"
        file_response = requests.get(raw_url)
        folder = raw_url.split("/")[-2]

        if file_response.status_code == 200:
            # print(base_path + folder + "-" + file.split("/")[-1])
            os.makedirs("Resume_Scrapper/Downloaded/code_files", exist_ok=True)
            with open(base_path + file_name + "-" + folder + "-" + file.split("/")[-1], "wb") as f:
                f.write(file_response.content)
            # print(f"Downloaded: {file}")
        else:
            print(f"Failed to download: {file}")
    
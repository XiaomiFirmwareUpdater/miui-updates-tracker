git grep 'bigota*' $(git rev-list --all) | grep -Po 'https?.*\.[a-z]*' | sort -u > links.txt 

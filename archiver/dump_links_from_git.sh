git grep 'bigota*' $(git rev-list --all) > roms.txt
cat roms.txt | grep -Po 'https?.*\.[a-z]*' | sort -u > links.txt 

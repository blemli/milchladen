# Galaxus.py

*The missing cli client for galaxus.ch*

![image-20250424181259146](milchladen.png)



# Install

## with pipx

```bash
# 1. clone and enter
git clone https://github.com/blemli/milchladen && cd milchladen

# 2. install
pipx install --editable .
```



## or with manual venv

```bash
# 1. clone and enter
git clone https://github.com/blemli/milchladen && cd milchladen

# 2. create venv
python3 -m venv .venv
source .venv/bin/activate

# 3. install dependencies
python3 -m pip install -r requirements.txt

# 4. make it executable
chmod +x galaxus.py

# 5. create alias
alias galaxus=./galaxus.py
```



# Use

```bash
galaxus auth login
galaxus --help
```

tohecho (toh) is your personal assistant to help you get your project work done faster

### Focus
* Jira
* Personal Todo List
* Calendar
* Email

### Principles
* We stay out of the user interface whenever possible, e.g. we comment on Jira, we send an email with an answer proposal
* We support local operations without the need for remote systems
* Ability to run self-hosted
* Ability to develop without internet connectivity
* No Admin need to ask, you can just run it


### Milestone one: 100 happy product managers
* we have 100 product managers using this solutions, they are liking it and would not want to miss it, they use it at least once a working wee
* we enable for them the following tasks with LLM
** what work finished in the last week and write a blog post for it?
** what work looks the most important to wrap up or spilled over?
** what is the overall project status?

### Disclaimer
Yes we read about the list of numerous Todo apps and productivity solutions, that never were to be.

* Chandler, a software project created by the Open Source Applications Foundation (OSAF).
* Google Wave, launched in 2009, aimed to combine email, instant messaging, document collaboration, and social networking into a single platform.
* Constellation by Netscape in the late 1990s to create a fully integrated desktop environment built on the web. It aimed to replace traditional operating systems with a web-first model.
* Microsoft Bob, Microsoft to simplify personal computing by creating a user interface that mimicked a home environment with rooms and objects representing tasks.
* Lotus Agenda personal information manager from Lotus in the late 1980s that allowed users to categorize and organize information based on flexible, user-defined rules.
* Obsidian, A markdown-based note-taking app with an emphasis on linking notes to create a "personal knowledge graph."
* Evernote, One of the earliest and most popular digital note-taking apps, allowing users to save, organize, and access information across devices.

### Read
https://medium.com/@anna_backtosenses/how-the-seductive-allure-of-productivity-porn-makes-you-less-productive-and-more-miserable-951797f73007

## Setup and Installation

1. Create a virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:
- On macOS/Linux:
```bash
source .venv/bin/activate
```
- On Windows:
```bash
.venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

To start the Chainlit application:

```bash
chainlit run app.py
```

The application will be available at http://localhost:8000

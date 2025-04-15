what features are missing for: Having github icon on toolbar's very left side.
Pressing on it -> Opens dialog with tabs / API / Projects / Monitoring / PR & Branch Settings / Events /
API: API key input with validation
Projects - Lists all account's projects and hooks to all them. 
Allows project selection and Button "Add To Toolbar" pressing which add's project representative icon to the middle of toolbar. When that project gets PR or new branch - Icon on the project's icon appears - notificationary. (Also - on the very right side, notification also appears (General)). 

Monitoring — allows selecting (
Notifications ON when
New PR [X] 
New Branch [X] 

(Both set on by defauly).
When pressing on notification -> Directs to original PR / Branch Page
PR & Branch Settings
Auto-merge rules - Automerge when updated files end only in .md and .prompt and have no actual codefiles - [ X ]
(if for example readme.md and generate.prompt are in PR - Auto-merge it if selected.

Events tab -> 
Allows creating events 
Create event button 
Created event's turn on/off feature
Delete event feature
rename event feature
Edit event feature

When pressing create -> 
Opens dialog  node area -> Add Node (Dropdown selection from - Projects, Prompts , Actions, Conditionals(Triggers) -
For example to be able to select project - add it as node
To add Conditional(Trigger) -Auto-merge or merge (Completed)
to add action -> analyze content -> selecting (validating merge items) -> View Last Merge (Repo Items) ->(To add Conditional) - 
If it was (Text Input) -Add Action (Send Prompt)-Select Prompt from prompt plugin list - (target) -> Coordinates  on tesktop where the system clicks and inputs prompt and presses enter.

  If it was (Text Input2) -Add Action (Send Prompt2)-Select Prompt from prompt plugin list - (target) -> Linear API (Target - Project selection -(Project Itself). / Issue title - Project name + issue content - prompt


       If it was (Text Input3) -Add Action (Send Prompt)-Select Prompt from prompt plugin list - (target) -> Coordinates  on tesktop where the system clicks and inputs prompt and presses enter.

Basicallly to be able to dynamically add rules & elements in regards to 4 plugin functionalities 
Github / linear / PromptGen / AutomationScript / 
And react to PR / New-Branch events - by sending dynamically conditionally selectable prompts to selected locations on desktop's chat input interfaces (As sendable messages) or via linear (As issues). 

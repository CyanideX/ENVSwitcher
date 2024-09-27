# env_switcher
 Switch envparams and customize your weather!


![ENVSwitcher](https://github.com/user-attachments/assets/9bc03fcc-c422-47b8-8957-8012003a9b5e)


 # How to use it:
 First, in WolvenKit, convert your master .env file to json format. Ensure that there are `.envparam` files in your project; the Weather State Manager will look for those in the same project directory as your env json and populate the lists accordingly.

 Run `main.py` and select the location of your master env.json.

 Select disabled weather state in the left listbox and move them to the active list by clicking the right arrow (`>>>`). You can disable states by moving them to the disable states list by clicking the left arrow (`<<<`). Click `Save` to confirm changes. Default vanilla states are greyed out and cannot be removed to avoid breaking the game.

 Any states added to the active list will be given default transition parameters.

 To edit transitions between states, click the `Transitions` button. Select a state in the middle listbox to see the states it can transition from (left checkbox) and to (right checkbox). You can enable the checkbox of any connecting states and click `Save` to confirm selection.

 To edit the properties of weather states, such as min/max duration, transition probability, transition duration, and weather effect particles, click the `Properties` button. Select the state in the left listbox to see current values. Values left blank when saving will save the correct null values in place of the tree.

 Alternatively, you may click the `Debug` button to apply global values for all weather states.

 To edit master film grain setting, click 'Film Grain'. The available resolution data will be loaded.

 You can toggle state HandleID tooltips by clicking `Enable Tooltips`.

 Reload the json if you're not seeing updates after saving the json externally.

 Click `Select JSON` to pick a new master env.json file.


 The `Export States` button is only there to generate a Nova City specific weather file.

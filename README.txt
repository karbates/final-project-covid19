Program Name: COVID-19 Dashboard for SI 507
Student: Karen Bates
Uniqname: karbates


Project Description:
This project is an attempt to aggregate data on COVID-19 from the COVID-19 Tracking API and
contextualize it with state health status data. It also shows recent Tweets from the CDC and a selected
state's health department, recent top headlines related to COVID-19, and graphs of positive cases in a state,
currently hospitalized cases, recovered people, and deaths in that state.


Imported Tools:
This program uses Flask (render_template, request), requests, Beautiful soup, OAuth1, sqlite3, and plotly,
in addition to several built-in packages.

This program uses the Twitter API and NewsAPI which require API keys to run. Mine are included in my secrets.py file
which is in the .gitignore file.


Instructions:
Please download the final_project_app.py program, the templates, and the csv files as named,
and save all in one folder.

Launch the final_project_app.py program from the terminal and use the link to see the html webpage
and interact with the program.

Close the webpage and press CTRL+C in the terminal to quit the program.

Interaction with Program:
At the home page of the app, a user can select the state from a drop down menu that they would like to see more COVID-19 information on.
They also have the option to select Tweet's from the CDC, Tweet's from the respective state's health department, and contextual health
status and hospital bed information for the state. Upon submitting the form, the user is taken to a page displaying the information
they selected. If they want, they can also navigate to a page with headlines relating to COVID-19 and plotted results for the number
of confirmed cases, hospitalized cases, recovered cases, and deaths as a result of COVID-19.
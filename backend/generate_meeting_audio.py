import pyttsx3

meetings = {
    "meeting1.wav": """
    Good morning team. Let's review the progress of the e-commerce application.
    Raj, please complete the product listing page and integrate the search functionality by June 20th.
    Meena, finish testing the checkout and payment modules by June 22nd.
    Rahul, prepare the database optimization report and share it with the team by June 25th.
    Priya, update the deployment documentation before June 21st.
    We will have a follow-up review meeting next Monday.
    Thank you everyone.
    """,

    "meeting2.wav": """
    Welcome everyone. Today we are discussing the banking application release.
    John, complete the transaction API integration by June 19th.
    Sarah, finish validating the account creation workflow by June 21st.
    David, prepare the security testing report by June 24th.
    Emily, update the user manual and release notes by June 23rd.
    We need all pending work completed before the final deployment scheduled next week.
    """,

    "meeting3.wav": """
    Good afternoon team. We are reviewing the hospital management system milestones.
    Karthik, complete the patient registration module by June 20th.
    Ananya, finish testing the appointment scheduling feature by June 22nd.
    Rohit, prepare the database backup strategy document by June 26th.
    Sneha, update the dashboard interface and submit it for review by June 21st.
    Our next status review will be conducted on Friday.
    """,

    "meeting4.wav": """
    Good morning everyone. Today we are reviewing the inventory management project.
    Arjun, complete the stock tracking feature and submit it by June 21st.
    Kavya, finish testing the warehouse management module by June 23rd.
    Vivek, prepare the API documentation and share it with the team by June 24th.
    Neha, update the reporting dashboard before June 22nd.
    We expect all critical tasks to be completed before the client demonstration scheduled next week.
    """,

    "meeting5.wav": """
    Hello team. Let's discuss the mobile application progress.
    Rahul, complete the login and authentication screens by June 20th.
    Priya, finish testing push notifications and messaging features by June 22nd.
    Akash, prepare the deployment checklist and infrastructure report by June 25th.
    Divya, update the user onboarding flow and submit it for review by June 21st.
    We will conduct the final readiness review meeting next Tuesday.
    """
}

engine = pyttsx3.init()

engine.setProperty("rate", 150)

for filename, text in meetings.items():
    engine.save_to_file(text, filename)

engine.runAndWait()

print("All WAV files generated successfully.")
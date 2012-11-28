Feature: sign up
  Scenario: as a user I want to be able to sign up for recall
    When i sign up
    Then i get an email
    And i have an account
    And only i can see my private email address

Feature: sign up
  Scenario: sign up for recall
    When i sign up
    Then i get an email
    And i have an account
    And only i can see my private email address

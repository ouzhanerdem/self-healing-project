# language: en

@restaurants
Feature: TGO Yemek Restaurants Page Tests
  Tests to ensure the Restaurants page of the TGO Yemek application
  is working correctly

  Scenario: Access and listing of Restaurants page
    Given I open the TGO Yemek restaurants page
    Then the page title should be "Yemek - Trendyol Go"
    And at least 1 restaurant should be listed on the page

  Scenario: Restaurant search function
    Given I open the TGO Yemek restaurants page
    When I type "pizza" in the search box
    And I click on the search button
    Then restaurants related to "pizza" should be displayed in the results

  Scenario: Viewing restaurant detail page
    Given I open the TGO Yemek restaurants page
    When I click on the first restaurant from the list
    Then the restaurant detail page should open
    And the restaurant information should be displayed

  Scenario: Checking pagination feature
    Given I open the TGO Yemek restaurants page
    When I go to the second page if pagination exists
    Then the second page restaurants should be displayed 
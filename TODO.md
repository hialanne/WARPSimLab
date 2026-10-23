# TODO 7850

This file collects project notes and cleanup items. Items here may later move into
GitHub issues, documentation files, or release plans.

* Add another mode.  Basic/ Standard/ Advanced.

* In Tax Report, elaborate on IRMAA, what bucket of IRMAA you are in, All of the buckets as a table, 
*   what the thresnold to upper and lower buckets are.

* Broader withdrawal strategies.  Not too many.  Keep them 
     user friendly.  Constant Dollar, Percent of Portfolio, VPW, Dynamic SWR, 
     Guyton-Klinger, CAPE-based spending, Vanguard Dynamic Spending,
* Create a report on withdrawal strategies
* Create a longevity report.
* Create an inheritance report.
* An update procedure isn't a bad idea. There is nuance, however.
* Replicate, and document, where the tables and means and standard deviations come from.
* More details on historical window
* Mac .dmg
* Create a Historical Stress Explorer.  Allow users to select retirement or simulation periods and see how it would survive 
* Refactor the Simulation object
* Possible Retirement Timeline Explorer
* Maybe more complex withdrawal order?

ACA + IRMAA integration. These are natural extensions of a detailed retirement cash-flow simulator. 
  They don't require WARPSimLab to become an optimizer. A year-by-year report showing MAGI, IRMAA tier/cost and 
  ACA subsidy effects would fit WARPSimLab very naturally.
Roth-conversion comparison/ensemble analysis rather than optimization. Instead of saying "the correct 
  conversion is $78,430," WARPSimLab could eventually evaluate a matrix such as 
  conversion strategy × retirement age × claiming age or conversion bracket × years. That stays consistent 
  with WARPSimLab's philosophy.
After-tax legacy value. Optimizer explicitly considers the different tax character of the assets left at the end. 
  That is much more meaningful than treating "$1M remaining" as equivalent regardless of whether it's 
  taxable, Tax-Deferred, Roth or HSA. Its new after-tax legacy constraint is conceptually quite good.



A short, high-value GUI feature list:

* **Medical / health-care expenses**

  * Pre-Medicare health insurance
  * Medicare premiums
  * IRMAA
  * Long-term-care / recurring medical costs

* **More explicit life-event expenses**

  * Home purchase
  * Home sale
  * Major remodel
  * Vehicle purchase
  * College / family support
  * One-time large expenses

* **More explicit income types**

  * Rental income
  * Inheritance
  * Consulting / part-time work
  * Royalties
  * Trust income
  * One-time windfalls

* **Debt and mortgage**

  * Mortgage balance/rate/payment
  * Other debt
  * Payoff date
  * Optional early payoff event

* **Portfolio transaction events**

  * Large taxable-account contribution
  * Large withdrawal
  * Transfer between account types
  * Sale/purchase of real estate
  * Scheduled asset-allocation changes

* **Survivor transition**

  * Death year/age for either spouse
  * Income streams that stop/change
  * Expense reduction
  * Filing-status change
  * Survivor Social Security/pension behavior

* **Better Social Security input**

  * FRA benefit amount
  * Claiming age
  * Spousal/survivor benefit fields
  * Possibly SSA-estimate based inputs

* **Expense categories**

  * Housing
  * Medical
  * Travel
  * Taxes
  * Discretionary
  * Other
  * Each optionally changing by age/year



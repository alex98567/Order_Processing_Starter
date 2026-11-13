Defects:
1. Quantity is not validated in cart.py. Any negative number or non integer could be passed without being checked. 
I fixed this by adding input validation raising a ValueError if any quantity that isn't a positive integer is entered.
2. There is a bug with how FREESHIP is applied. It currently prints a message saying that shipping is free but doesn't
actually do anything to amount. The logic also appears to freeze the price at whatever it was at when FREESHIP was applied,
regardless of items added or subtracted from the cart. I fixed this by separating price discounts from perks (such as
free shipping) by introducing self.free_shipping flag.
3. The logic appears to freeze the price at whatever it was at whenever a coupon was applied (WELCOME10, STUDENT20, 
and SAVE15), regardless of items added or subtracted from the cart. I removed self.discounted_total entirely and refactored total() to calculate coupon rules against the 
running subtotal on each call.
4. I noticed that this program uses primitive Python float types for everything currency related. This can technically 
lead to rounding errors which can over time lead to drift and mismatching invoices. 
I fixed this by using decimal.Decimal instead to cart.py and models.py.
5. repository.py appears to have a SQL injection vulnerability using direct string formatting (f"..."). I corrected it
by replacing the vulnerabilities with safe, parameterized queries using SQLite's question-mark placeholders to ensure 
user inputs are always treated as data instead of potentially executable SQL code.
6. In checkout.py, stock is decremented before payment is processed, and is never reset if there's an error with payment. I fixed this 
by restructuring the checkout workflow so that inventory is only updated after confirming payment status has successfully
returned 'paid'.
7. Similarly to defect 6, a user's cart clears before payment is processed. If there is a payment error and the user 
wants to correct that and continue with their cart, they currently would come back to an empty cart. I fixed this by 
only clearing the cart after payment is processed.
8. The checkout() method accepts request_id as a parameter but never actually does anything with it, potentially 
resulting in errors. I fixed this by passing the parameter into the save_order, storing it alongside the order record.

Test Results (Including the 2 from test_smoke.py:
PS C:\Users\Alex Howe\Downloads\Order_Processing_Starter\Order_Processing_Starter> python -m pytest -q       
..............                                                                                                                                                               [100%]
14 passed in 0.28s

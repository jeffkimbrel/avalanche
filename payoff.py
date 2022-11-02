#!/usr/bin/env python3

import argparse
import json
import sys
from functools import reduce
from operator import add

parser = argparse.ArgumentParser(description="""
This tool takes in a list of debts (see DEBT) and uses the avalanche 
philosophy of debt management to pay off debts. Each time a debt is 
paid off, its payment amount (along with any EXTRA) will be put towards 
the next highest paying debt.""", formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('-d', '--debt',
                    help="""
The file detailing debts in a JSON array format. Each element in the 
array must have a debt name `name`, debt amount `amount`, interest 
rate `rate`, and a minimum payment `payment`.""", required=True)

parser.add_argument('-e', '--extra',
                    help="The extra amount to be paid each month, which will be allocated to the next highest debt.",
                    required=False,
                    default=0,
					type = float)

args = parser.parse_args()

def print_table(debts, extra_payments):
	zero_balance = False
	
	print_row_str((debt['name'] for debt in debts), '\n')
	
	# each iteration is a month
	while not zero_balance:
		zero_balance = all(debt['amount'] == 0 for debt in debts)

		# show monthly balance before any interest or payments
		print_balances(debts, 'starting amount')

		# calculate and show monthly interest
		interest = calculate_interest(debts)
		print_row_float(interest, 'interest')

		# add interest to the debt (this assumes monthly compounding)
		apply(debts, interest)
		print_balances(debts, 'new amount')

		# show minimum payments, then take them out of remaining debt
		minimum_payments = calculate_minimum_payments(debts)
		unused_payments = calculate_unused_payments(debts, minimum_payments)
		apply(debts, minimum_payments)
		print_row_float(minimum_payments, 'minimum payments')
		
		excess = calculate_excess(debts, unused_payments + extra_payments)
		print_row_float(excess, 'excess payments')

		# reduce highest rate debts first (debts were sorted by rate)
		apply(debts, excess)
		print_balances(debts, 'ending amount')
		
		print()

def print_row_str(values, end, colsep=' | '):
	for value in values:
		print('{:>12}'.format(value), end=colsep)
	print(end)

def print_row_float(values, end, colsep=' | '):
	for value in values:
		print('{:12.2f}'.format(value), end=colsep)
	print(end)

def print_balances(debts, end):
	print_row_float((debt['amount'] for debt in debts), end)

def calculate_interest(debts):
	return [debt['amount'] * (debt['rate'] / 12) if debt['amount'] > 0 else 0 for debt in debts]

def calculate_minimum_payments(debts):
	return [-min(debt['payment'], debt['amount']) for debt in debts]

def calculate_unused_payments(debts, minimum_payments):
	return reduce(add, map(add, minimum_payments, (debt['payment'] for debt in debts)))

def calculate_excess(debts, excess):
	excess_payments = []
	for debt in debts:
		if debt['amount'] > 0 and excess > 0:
			if excess > debt['amount']:
				excess_payments.append(-debt['amount'])
				excess = excess - debt['amount']
			else:
				excess_payments.append(-excess)
				excess = 0
		else:
			excess_payments.append(-0.0)

	return excess_payments

def apply(debts, amount):
	for i in range(len(debts)):
		debts[i]['amount'] = debts[i]['amount'] + amount[i]

def load_debts(file_name):
	debts = None
	with open(file_name) as debt_file:
		# sort the debt by rate, highest rate first
		debts = sorted(json.load(debt_file), key=lambda d: d['rate'], reverse=True)
	return debts

if __name__ == '__main__':
	debts = load_debts(args.debt)
	print_table(debts, args.extra)
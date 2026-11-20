
"""
PARAORDER: E-COMMERCE ORDER PROCESSING

Sequential and Parallel Processing Comparison

Processing methods:
1. Sequential Processing
2. Manual Multithreading
3. Multiprocessing Pool
4. ThreadPoolExecutor
5. ProcessPoolExecutor

Performance metrics:
- Execution Time
- Speedup
- Parallel Efficiency
- Completed Orders
- Invalid Orders
- Out-of-Stock Orders
- Flagged Orders
- Total Confirmed Sales
"""

import os
import time
import random
import hashlib
import threading
import multiprocessing

from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


# ============================================================
# 1. CONFIGURATION
# ============================================================

BATCH_SIZES = [10_000, 50_000, 100_000]

# Test different worker counts, limited by available CPU cores.
CPU_COUNT = os.cpu_count() or 2

WORKER_COUNTS = [
    workers
    for workers in [1, 2, 4, 8, 16]
    if workers <= CPU_COUNT
]

# CPU-intensive simulation workload.
HASH_ROUNDS = 3

# VAT rate
VAT_RATE = 0.12

# Fraud detection thresholds
FRAUD_AMOUNT_THRESHOLD = 100_000
FRAUD_ITEM_THRESHOLD = 12

# Product catalog
PRODUCTS = {
    "Laptop": 45000,
    "Smartphone": 25000,
    "Headphones": 2500,
    "Keyboard": 1500,
    "Mouse": 800,
    "Monitor": 12000,
    "Tablet": 18000,
    "Smartwatch": 5500,
    "Speaker": 3200,
    "Webcam": 2200
}

# Shipping fees based on customer region
SHIPPING_FEES = {
    "NCR": 80,
    "Luzon": 120,
    "Visayas": 180,
    "Mindanao": 220
}


# ============================================================
# 2. GENERATE SIMULATED CUSTOMER ORDERS
# ============================================================

def generate_orders(number_of_orders):
    """
    Generates simulated e-commerce customer orders.

    Each order contains:
    - Order ID
    - Customer information
    - Product names
    - Product quantities
    - Product prices
    - Available stock
    - Customer region
    - Voucher discount rate

    A small number of invalid and out-of-stock orders
    are intentionally generated for testing.
    """

    rng = random.Random(42 + number_of_orders)

    regions = list(SHIPPING_FEES.keys())
    product_names = list(PRODUCTS.keys())

    orders = []

    for i in range(1, number_of_orders + 1):

        customer = {
            "customer_id": f"CUST-{i:06d}",
            "name": f"Customer {i}"
        }

        selected_products = rng.sample(
            product_names,
            rng.randint(1, 4)
        )

        items = []

        for product_name in selected_products:

            quantity = rng.randint(1, 5)
            price = PRODUCTS[product_name]

            available_stock = rng.randint(1, 8)

            # Generate some out-of-stock orders.
            if i % 10 == 0:
                available_stock = max(0, quantity - 1)

            # Generate some invalid orders.
            if i % 100 == 0:
                quantity = 0

            items.append({
                "product_name": product_name,
                "quantity": quantity,
                "price": price,
                "available_stock": available_stock
            })

        order = {
            "order_id": f"ORD-{i:06d}",
            "customer": customer,
            "region": rng.choice(regions),
            "voucher_rate": rng.choice([0.00, 0.05, 0.10]),
            "items": items
        }

        orders.append(order)

    return orders


# ============================================================
# 3. STEP 1: VALIDATE ORDER
# ============================================================

def validate_order(order):
    """
    Checks whether an order contains complete and valid details.

    Validation includes:
    - Order ID
    - Customer information
    - Region
    - Voucher rate
    - Product names
    - Quantities
    - Prices
    - Available stock values
    """

    if not isinstance(order, dict):
        return False

    if not order.get("order_id"):
        return False

    customer = order.get("customer")

    if not isinstance(customer, dict):
        return False

    if not customer.get("customer_id"):
        return False

    if not customer.get("name"):
        return False

    if order.get("region") not in SHIPPING_FEES:
        return False

    voucher_rate = order.get("voucher_rate")

    if (
        not isinstance(voucher_rate, (int, float))
        or isinstance(voucher_rate, bool)
        or not 0 <= voucher_rate <= 1
    ):
        return False

    items = order.get("items")

    if not isinstance(items, list) or not items:
        return False

    for item in items:

        if not isinstance(item, dict):
            return False

        if item.get("product_name") not in PRODUCTS:
            return False

        quantity = item.get("quantity")
        price = item.get("price")
        stock = item.get("available_stock")

        if (
            not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity <= 0
        ):
            return False

        if (
            not isinstance(price, (int, float))
            or isinstance(price, bool)
            or price < 0
        ):
            return False

        if (
            not isinstance(stock, int)
            or isinstance(stock, bool)
            or stock < 0
        ):
            return False

    return True


# ============================================================
# 4. STEP 2: CHECK PRODUCT STOCK
# ============================================================

def check_stock(order):
    """
    Checks whether the requested product quantities
    are within the available stock.
    """

    for item in order["items"]:

        if item["quantity"] > item["available_stock"]:
            return False

    return True


# ============================================================
# 5. STEP 3: COMPUTE ORDER TOTAL
# ============================================================

def calculate_order_total(order):
    """
    Calculates:
    1. Subtotal
    2. Voucher discount
    3. Discounted subtotal
    4. 12% VAT
    5. Region-based shipping fee
    6. Final order total
    """

    subtotal = sum(
        item["quantity"] * item["price"]
        for item in order["items"]
    )

    discount = subtotal * order["voucher_rate"]

    discounted_subtotal = subtotal - discount

    vat = discounted_subtotal * VAT_RATE

    shipping_fee = SHIPPING_FEES[order["region"]]

    final_total = (
        discounted_subtotal
        + vat
        + shipping_fee
    )

    return {
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "vat": round(vat, 2),
        "shipping_fee": round(shipping_fee, 2),
        "final_total": round(final_total, 2)
    }


# ============================================================
# 6. STEP 4: FRAUD CHECK
# ============================================================

def check_fraud(order, financial_details):
    """
    Flags suspicious orders based on:
    - Very large transaction amounts
    - Unusually high total product quantities
    """

    total_quantity = sum(
        item["quantity"]
        for item in order["items"]
    )

    if (
        financial_details["final_total"]
        >= FRAUD_AMOUNT_THRESHOLD
    ):
        return True

    if total_quantity >= FRAUD_ITEM_THRESHOLD:
        return True

    return False


# ============================================================
# 7. STEP 5: GENERATE ORDER SUMMARY
# ============================================================

def process_order(order):
    """
    Executes all five order-processing steps.

    Possible order statuses:
    - Invalid
    - Out of Stock
    - Flagged
    - Completed

    Only Completed orders contribute to confirmed sales.
    """

    # STEP 1: Validate
    if not validate_order(order):

        return {
            "order_id": order.get("order_id", "UNKNOWN"),
            "customer": order.get("customer", {}),
            "items": order.get("items", []),
            "subtotal": 0,
            "discount": 0,
            "vat": 0,
            "shipping_fee": 0,
            "final_total": 0,
            "status": "Invalid"
        }

    # STEP 2: Check stock
    if not check_stock(order):

        return {
            "order_id": order["order_id"],
            "customer": order["customer"],
            "items": order["items"],
            "subtotal": 0,
            "discount": 0,
            "vat": 0,
            "shipping_fee": 0,
            "final_total": 0,
            "status": "Out of Stock"
        }

    # STEP 3: Compute total
    financial_details = calculate_order_total(order)

    # STEP 4: Fraud check
    is_flagged = check_fraud(order, financial_details)

    # STEP 5: Generate summary
    if is_flagged:
        status = "Flagged"
    else:
        status = "Completed"

    # Simulated CPU workload for performance comparison.
    # This is not an actual fraud detection algorithm.
    payload = (
        f"{order['order_id']}"
        f"{financial_details['final_total']}"
    ).encode()

    digest = payload

    for _ in range(HASH_ROUNDS):
        digest = hashlib.sha256(digest).digest()

    return {
        "order_id": order["order_id"],
        "customer": order["customer"],
        "items": order["items"],
        "subtotal": financial_details["subtotal"],
        "discount": financial_details["discount"],
        "vat": financial_details["vat"],
        "shipping_fee": financial_details["shipping_fee"],
        "final_total": financial_details["final_total"],
        "status": status
    }


# ============================================================
# 8. PROCESS A CHUNK OF ORDERS
# ============================================================

def process_orders_chunk(order_chunk):
    """
    Processes all orders inside one assigned chunk.

    Used by the parallel implementations.
    """

    return [
        process_order(order)
        for order in order_chunk
    ]


# ============================================================
# 9. DIVIDE ORDERS INTO CHUNKS
# ============================================================

def divide_into_chunks(orders, number_of_chunks):
    """
    Divides a dataset into balanced chunks.

    Each worker receives one chunk of orders.
    """

    number_of_chunks = min(
        max(1, number_of_chunks),
        len(orders)
    )

    base_size, remainder = divmod(
        len(orders),
        number_of_chunks
    )

    chunks = []
    start = 0

    for i in range(number_of_chunks):

        chunk_size = base_size

        if i < remainder:
            chunk_size += 1

        end = start + chunk_size

        chunks.append(orders[start:end])

        start = end

    return chunks


# ============================================================
# 10. METHOD 1: SEQUENTIAL PROCESSING
# ============================================================

def sequential_processing(orders):
    """
    Processes orders one at a time using a single loop.

    Each order must finish before the next order begins.
    """

    results = []

    for order in orders:
        results.append(process_order(order))

    return results


# ============================================================
# 11. METHOD 2: MANUAL MULTITHREADING
# ============================================================

def manual_multithreading(orders, workers):
    """
    Uses threading.Thread to process order chunks.

    Each thread receives its own group of orders.
    """

    chunks = divide_into_chunks(orders, workers)

    results = [None] * len(chunks)
    errors = []

    def worker_function(chunk, index):

        try:
            results[index] = process_orders_chunk(chunk)

        except Exception as error:
            errors.append(error)

    threads = []

    for index, chunk in enumerate(chunks):

        thread = threading.Thread(
            target=worker_function,
            args=(chunk, index)
        )

        threads.append(thread)
        thread.start()

    # Wait for every thread to finish.
    for thread in threads:
        thread.join()

    if errors:
        raise RuntimeError(
            f"Thread processing failed: {errors[0]}"
        )

    # Combine results from all threads.
    final_results = []

    for chunk_result in results:
        final_results.extend(chunk_result)

    return final_results


# ============================================================
# 12. METHOD 3: MULTIPROCESSING POOL
# ============================================================

def multiprocessing_pool(orders, workers):
    """
    Uses multiprocessing.Pool to distribute order chunks
    across multiple independent CPU processes.
    """

    chunks = divide_into_chunks(orders, workers)

    with Pool(processes=workers) as pool:

        chunk_results = pool.map(
            process_orders_chunk,
            chunks
        )

    final_results = []

    for chunk_result in chunk_results:
        final_results.extend(chunk_result)

    return final_results


# ============================================================
# 13. METHOD 4: THREAD POOL EXECUTOR
# ============================================================

def thread_pool_executor(orders, workers):
    """
    Uses ThreadPoolExecutor to manage worker threads.

    The executor assigns chunks to available threads.
    """

    chunks = divide_into_chunks(orders, workers)

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        chunk_results = list(
            executor.map(
                process_orders_chunk,
                chunks
            )
        )

    final_results = []

    for chunk_result in chunk_results:
        final_results.extend(chunk_result)

    return final_results


# ============================================================
# 14. METHOD 5: PROCESS POOL EXECUTOR
# ============================================================

def process_pool_executor(orders, workers):
    """
    Uses ProcessPoolExecutor to distribute order chunks
    among multiple independent CPU processes.
    """

    chunks = divide_into_chunks(orders, workers)

    with ProcessPoolExecutor(
        max_workers=workers
    ) as executor:

        chunk_results = list(
            executor.map(
                process_orders_chunk,
                chunks
            )
        )

    final_results = []

    for chunk_result in chunk_results:
        final_results.extend(chunk_result)

    return final_results


# ============================================================
# 15. GENERATE ORDER REPORT
# ============================================================

def generate_report(results):
    """
    Counts all order statuses and calculates confirmed sales.

    Confirmed sales include Completed orders only.
    Flagged, Invalid, and Out of Stock orders are excluded.
    """

    report = {
        "total_orders": len(results),
        "completed": 0,
        "invalid": 0,
        "out_of_stock": 0,
        "flagged": 0,
        "confirmed_sales": 0.0
    }

    for result in results:

        status = result["status"]

        if status == "Completed":

            report["completed"] += 1

            report["confirmed_sales"] += (
                result["final_total"]
            )

        elif status == "Invalid":

            report["invalid"] += 1

        elif status == "Out of Stock":

            report["out_of_stock"] += 1

        elif status == "Flagged":

            report["flagged"] += 1

    report["confirmed_sales"] = round(
        report["confirmed_sales"],
        2
    )

    return report


# ============================================================
# 16. VALIDATE RESULTS BETWEEN METHODS
# ============================================================

def calculate_result_signature(results):
    """
    Creates a checksum based on the ordered results.

    This helps verify that different processing methods
    return the same order statuses and final totals.
    """

    signature = hashlib.sha256()

    for result in results:

        record = (
            result["order_id"],
            result["status"],
            result["final_total"]
        )

        signature.update(
            repr(record).encode()
        )

        signature.update(b"\n")

    return signature.hexdigest()


def validate_results(reference_signature, test_results):
    """
    Checks whether the current method produces the same
    per-order results as sequential processing.
    """

    test_signature = calculate_result_signature(
        test_results
    )

    return reference_signature == test_signature


# ============================================================
# 17. MEASURE EXECUTION TIME
# ============================================================

def measure_execution(function, *args):
    """
    Measures processing time using time.perf_counter().

    Returns:
    - Processing results
    - Execution time in seconds
    """

    start_time = time.perf_counter()

    results = function(*args)

    end_time = time.perf_counter()

    execution_time = end_time - start_time

    return results, execution_time


# ============================================================
# 18. DISPLAY SAMPLE ORDERS
# ============================================================

def display_sample_orders(results):
    """
    Displays the first three processed customer orders.
    """

    print("\nSAMPLE PROCESSED ORDERS")
    print("-" * 65)

    for result in results[:3]:

        customer = result["customer"]

        print(f"\nOrder ID: {result['order_id']}")

        print(
            f"Customer: {customer.get('name', 'Unknown')}"
        )

        print("Products:")

        for item in result["items"]:

            print(
                f"  - {item['product_name']}"
                f" | Quantity: {item['quantity']}"
                f" | Price: PHP {item['price']:,.2f}"
            )

        print(
            f"Subtotal: PHP {result['subtotal']:,.2f}"
        )

        print(
            f"Discount: PHP {result['discount']:,.2f}"
        )

        print(
            f"VAT: PHP {result['vat']:,.2f}"
        )

        print(
            f"Shipping: PHP {result['shipping_fee']:,.2f}"
        )

        print(
            f"Final Total: PHP {result['final_total']:,.2f}"
        )

        print(f"Status: {result['status']}")

    print("-" * 65)


# ============================================================
# 19. DISPLAY PERFORMANCE AND ORDER REPORTS
# ============================================================

def display_performance_table(sequential_time, results, workers):
    print("\n" + "=" * 100)
    print("                         PERFORMANCE COMPARISON")
    print("=" * 100)

    print(
        f"{'Processing Method':<25}"
        f"{'Execution Time':<18}"
        f"{'Speedup':<13}"
        f"{'Efficiency':<15}"
        f"{'Flagged Orders':<15}"
    )
    print("-" * 100)

    # Sequential baseline
    sequential_flagged = sum(
        1 for result in sequential_results
        if result["status"] == "Flagged"
    )

    print(
        f"{'Sequential':<25}"
        f"{sequential_time:<18.4f}"
        f"{'1.00x':<13}"
        f"{'N/A':<15}"
        f"{sequential_flagged:<15}"
    )

    for method_name, execution_time, method_results in results:
        speedup = sequential_time / execution_time
        efficiency = (speedup / workers) * 100

        flagged = sum(
            1 for result in method_results
            if result["status"] == "Flagged"
        )

        print(
            f"{method_name:<25}"
            f"{execution_time:<18.4f}"
            f"{speedup:.2f}x{'':<9}"
            f"{efficiency:.2f}%{'':<9}"
            f"{flagged:<15}"
        )

    print("=" * 100)

# ============================================================
# 20. MAIN PROGRAM
# ============================================================

def main():

    all_benchmark_results = []

    print("\n")
    print("=" * 75)
    print("             PARAORDER: E-COMMERCE ORDER PROCESSING")
    print("       SEQUENTIAL AND PARALLEL PROCESSING COMPARISON")
    print("=" * 75)

    print(f"Available CPU cores: {CPU_COUNT}")
    print(f"Worker configurations: {WORKER_COUNTS}")
    print(f"Batch sizes: {BATCH_SIZES}")
    print(f"VAT Rate: {VAT_RATE * 100:.0f}%")

    # Run different dataset sizes.
    for batch_size in BATCH_SIZES:

        print("\n\n")
        print("#" * 75)
        print(f"GENERATING {batch_size:,} CUSTOMER ORDERS")
        print("#" * 75)

        # Generate one dataset for all processing methods.
        orders = generate_orders(batch_size)

        print(f"Generated orders: {len(orders):,}")

        benchmark_results = []

        # ----------------------------------------------------
        # METHOD 1: SEQUENTIAL PROCESSING
        # ----------------------------------------------------

        print("\nRunning Sequential Processing...")

        sequential_results, sequential_time = measure_execution(
            sequential_processing,
            orders
        )

        sequential_report = generate_report(
            sequential_results
        )

        reference_signature = calculate_result_signature(
            sequential_results
        )

        print(
            f"Sequential Execution Time: "
            f"{sequential_time:.4f} seconds"
        )

        print(
            f"Completed Orders: "
            f"{sequential_report['completed']:,}"
        )

        print(
            f"Invalid Orders: "
            f"{sequential_report['invalid']:,}"
        )

        print(
            f"Out-of-Stock Orders: "
            f"{sequential_report['out_of_stock']:,}"
        )

        print(
            f"Flagged Orders: "
            f"{sequential_report['flagged']:,}"
        )

        print(
            f"Confirmed Sales: PHP "
            f"{sequential_report['confirmed_sales']:,.2f}"
        )

        # Show a few examples.
        display_sample_orders(sequential_results)

        benchmark_results.append({
            "method": "Sequential",
            "workers": 1,
            "execution_time": sequential_time,
            "report": sequential_report
        })

        del sequential_results

        # ----------------------------------------------------
        # PARALLEL PROCESSING METHODS
        # ----------------------------------------------------

        parallel_methods = [
            (
                "Manual Multithreading",
                manual_multithreading
            ),
            (
                "Multiprocessing Pool",
                multiprocessing_pool
            ),
            (
                "ThreadPoolExecutor",
                thread_pool_executor
            ),
            (
                "ProcessPoolExecutor",
                process_pool_executor
            )
        ]

        # Test different worker counts.
        for workers in WORKER_COUNTS:

            print("\n")
            print("-" * 75)
            print(f"TESTING WITH {workers} WORKER(S)")
            print("-" * 75)

            for method_name, method_function in parallel_methods:

                print(f"\nRunning {method_name}...")

                parallel_results, execution_time = measure_execution(
                    method_function,
                    orders,
                    workers
                )

                # Generate the order summary.
                report = generate_report(
                    parallel_results
                )

                # Verify identical results.
                is_correct = validate_results(
                    reference_signature,
                    parallel_results
                )

                print(
                    f"Execution Time: {execution_time:.4f} seconds"
                )

                print(
                    f"Results Match Sequential: "
                    f"{'YES' if is_correct else 'NO'}"
                )

                if not is_correct:
                    raise RuntimeError(
                        f"{method_name} produced different results!"
                    )

                # Save all metrics.
                benchmark_results.append({
                    "method": method_name,
                    "workers": workers,
                    "execution_time": execution_time,
                    "report": report
                })

                del parallel_results

        # ----------------------------------------------------
        # DISPLAY COMPLETE DATASET REPORT
        # ----------------------------------------------------

        display_performance_table(
            sequential_time,
            benchmark_results,
            batch_size
        )

        all_benchmark_results.append({
            "batch_size": batch_size,
            "results": benchmark_results
        })

        del orders

    # ========================================================
    # 21. FINAL BENCHMARK SUMMARY
    # ========================================================

    print("\n\n")
    print("=" * 85)
    print("                  FINAL BENCHMARK SUMMARY")
    print("=" * 85)

    for dataset in all_benchmark_results:

        batch_size = dataset["batch_size"]
        results = dataset["results"]

        print(f"\nDataset: {batch_size:,} Orders")

        sequential_entry = results[0]

        print(
            f"Sequential Time: "
            f"{sequential_entry['execution_time']:.4f} seconds"
        )

        parallel_entries = results[1:]

        fastest = min(
            parallel_entries,
            key=lambda entry: entry["execution_time"]
        )

        print(f"Fastest Method: {fastest['method']}")

        print(f"Workers: {fastest['workers']}")

        print(
            f"Execution Time: "
            f"{fastest['execution_time']:.4f} seconds"
        )

        speedup = (
            sequential_entry["execution_time"]
            / fastest["execution_time"]
        )

        efficiency = speedup / fastest["workers"]

        print(f"Speedup: {speedup:.2f}x")

        print(f"Efficiency: {efficiency * 100:.2f}%")

    print("\n")
    print("=" * 85)
    print("             ALL ORDER PROCESSING TESTS COMPLETED")
    print("=" * 85)


# ============================================================
# 22. PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    multiprocessing.freeze_support()

    main()
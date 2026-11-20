
import os
import time
import random
import hashlib
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


# ============================================================
# 1. PROGRAM CONFIGURATION
# ============================================================

# Number of customer orders to be processed.
NUM_ORDERS = 30

# Get the number of available CPU cores.
# The number of workers is limited to the number of orders.
WORKERS = min(os.cpu_count() or 1, NUM_ORDERS)


# ============================================================
# 2. SAMPLE E-COMMERCE ORDER GENERATION
# ============================================================

def generate_orders():
    """
    Generates sample customer orders containing:
    - Order ID
    - Customer name
    - Customer location
    - Product names
    - Product quantities
    - Product prices

    A fixed random seed ensures that the same sample
    orders are generated every time the program runs.
    """

    random.seed(42)

    customers = [
        "John Smith", "Maria Santos", "James Brown",
        "Anna Garcia", "Michael Lee", "Sophia Cruz",
        "Daniel Reyes", "Isabella Tan", "David Miller",
        "Olivia Chen"
    ]

    cities = [
        "Manila", "Cavite", "Quezon City",
        "Makati", "Pasig", "Taguig"
    ]

    products = {
        "Laptop": 45000,
        "Smartphone": 25000,
        "Headphones": 3500,
        "Keyboard": 1800,
        "Mouse": 1200,
        "Monitor": 12000,
        "Webcam": 2500,
        "USB Drive": 500,
        "Charger": 900,
        "Speaker": 4000
    }

    orders = []

    for order_id in range(1, NUM_ORDERS + 1):

        # Randomly select products for each customer.
        selected_products = random.sample(
            list(products.items()),
            random.randint(1, 4)
        )

        items = []

        for product_name, price in selected_products:
            items.append({
                "product": product_name,
                "quantity": random.randint(1, 3),
                "price": price
            })

        order = {
            "order_id": order_id,
            "customer": random.choice(customers),
            "city": random.choice(cities),
            "items": items
        }

        orders.append(order)

    return orders


# ============================================================
# 3. ORDER PROCESSING FUNCTION
# ============================================================

def process_order(order):
    """
    Processes one customer order.

    Tasks performed:
    1. Calculate the subtotal.
    2. Apply discounts.
    3. Calculate shipping fees.
    4. Simulate payment processing.
    5. Perform a simulated checksum computation.
    6. Return the completed order details.

    This function is used by all processing methods.
    """

    # Create a copy of the order to avoid modifying
    # the original customer order.
    result = dict(order)

    # Calculate the total price of all products.
    subtotal = sum(
        item["quantity"] * item["price"]
        for item in order["items"]
    )

    # Apply discounts based on the order subtotal.
    discount = 0

    if subtotal >= 5000:
        discount = subtotal * 0.10

    elif subtotal >= 2000:
        discount = subtotal * 0.05

    # Calculate the total after applying the discount.
    discounted_total = subtotal - discount

    # Apply shipping fees.
    # Orders with a discounted total of at least 3000
    # receive free shipping.
    if discounted_total >= 3000:
        shipping_fee = 0
    else:
        shipping_fee = 150

    # Calculate the final order total.
    final_total = discounted_total + shipping_fee

    # Simulate payment processing or I/O waiting time.
    # This allows threads to demonstrate concurrent execution.
    time.sleep(0.08)

    # Simulate a CPU-intensive task using repeated SHA-256 hashing.
    # This represents additional processing such as
    # receipt verification or checksum computation.
    data = str(order["order_id"]).encode()

    for _ in range(150000):
        data = hashlib.sha256(data).digest()

    # Store the calculated information in the result.
    result["subtotal"] = subtotal
    result["discount"] = discount
    result["shipping_fee"] = shipping_fee
    result["final_total"] = final_total
    result["checksum"] = data.hex()[:16]
    result["status"] = "Completed"

    return result


# ============================================================
# 4. THREAD WORKER FUNCTION
# ============================================================

def thread_worker(order_list, results):
    """
    Worker function for manual multithreading.

    Each thread receives a portion of the customer orders
    and processes them one at a time.

    The processed orders are added to a shared results list.
    """

    for order in order_list:
        processed_order = process_order(order)
        results.append(processed_order)


# ============================================================
# 5. DISPLAY ORDER DETAILS
# ============================================================

def display_orders(results):
    """
    Displays the processed customer order information,
    including products, quantities, prices, discounts,
    shipping fees, final totals, and processing status.
    """

    print("\n" + "=" * 65)
    print("              E-COMMERCE ORDER PROCESSING")
    print("=" * 65)

    for order in results:

        print(f"\nOrder ID: {order['order_id']}")
        print(f"Customer: {order['customer']}")
        print(f"Location: {order['city']}")

        print("\nProducts:")

        for item in order["items"]:
            print(
                f"  - {item['product']} | "
                f"Quantity: {item['quantity']} | "
                f"Price: PHP {item['price']:,.2f}"
            )

        print(f"\nSubtotal: PHP {order['subtotal']:,.2f}")
        print(f"Discount: PHP {order['discount']:,.2f}")
        print(f"Shipping Fee: PHP {order['shipping_fee']:,.2f}")
        print(f"Final Total: PHP {order['final_total']:,.2f}")
        print(f"Status: {order['status']}")

    print("\n" + "=" * 65)
    print(f"Total Processed Orders: {len(results)}")
    print("=" * 65)


# ============================================================
# 6. PERFORMANCE MEASUREMENT FUNCTION
# ============================================================

def measure_time(function):
    """
    Measures the execution time of a processing method.

    time.perf_counter() provides a high-resolution timer
    suitable for measuring program execution time.

    Returns:
    - Processing results
    - Execution time in seconds
    """

    start_time = time.perf_counter()

    results = function()

    end_time = time.perf_counter()

    execution_time = end_time - start_time

    return results, execution_time


# ============================================================
# 7. SEQUENTIAL PROCESSING
# ============================================================

def sequential_processing(orders):
    """
    SEQUENTIAL PROCESSING

    Processes customer orders one at a time.

    The program must finish processing the current order
    before moving to the next order.

    This serves as the baseline for performance comparison.
    """

    results = []

    for order in orders:
        processed_order = process_order(order)
        results.append(processed_order)

    return results


# ============================================================
# 8. MULTITHREADING USING THREADING MODULE
# ============================================================

def multithreading_processing(orders):
    """
    MULTITHREADING

    Uses the threading module to create multiple threads.

    Each thread receives a portion of the customer orders.
    Threads execute concurrently and process their assigned orders.

    join() ensures that the main program waits until
    all threads have finished processing.
    """

    results = []

    threads = []

    # Create the worker threads.
    for worker_id in range(WORKERS):

        # Divide orders among threads using slicing.
        # Example: Thread 0 gets orders 0, 6, 12, etc.
        assigned_orders = orders[worker_id::WORKERS]

        thread = threading.Thread(
            target=thread_worker,
            args=(assigned_orders, results)
        )

        threads.append(thread)

    # Start all threads.
    for thread in threads:
        thread.start()

    # Wait for all threads to finish.
    for thread in threads:
        thread.join()

    return results


# ============================================================
# 9. MULTIPROCESSING USING MULTIPROCESSING MODULE
# ============================================================

def multiprocessing_processing(orders):
    """
    MULTIPROCESSING

    Uses the multiprocessing module to create separate
    processes that can run on multiple CPU cores.

    Pool() creates a group of worker processes.

    map() distributes customer orders among the processes
    and collects their results.
    """

    with multiprocessing.Pool(processes=WORKERS) as pool:

        results = pool.map(process_order, orders)

    return results


# ============================================================
# 10. THREADPOOL EXECUTOR
# ============================================================

def threadpool_processing(orders):
    """
    THREADPOOL EXECUTOR

    Uses ThreadPoolExecutor from concurrent.futures.

    It manages a pool of reusable threads instead of
    manually creating and managing individual threads.

    map() assigns the customer orders to available threads.
    """

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:

        results = list(executor.map(process_order, orders))

    return results


# ============================================================
# 11. PROCESSPOOL EXECUTOR
# ============================================================

def processpool_processing(orders):
    """
    PROCESSPOOL EXECUTOR

    Uses ProcessPoolExecutor from concurrent.futures.

    It manages a pool of separate worker processes
    that can execute tasks across multiple CPU cores.

    map() distributes the customer orders among processes.
    """

    with ProcessPoolExecutor(max_workers=WORKERS) as executor:

        results = list(executor.map(process_order, orders))

    return results


# ============================================================
# 12. RESULT VALIDATION
# ============================================================

def validate_results(sequential_results, parallel_results, method_name):
    """
    Checks whether the parallel implementation produces
    the same order totals as the sequential implementation.

    Sorting by Order ID makes the comparison independent
    of the order in which threads or processes finish.
    """

    sequential_totals = sorted(
        (order["order_id"], order["final_total"])
        for order in sequential_results
    )

    parallel_totals = sorted(
        (order["order_id"], order["final_total"])
        for order in parallel_results
    )

    assert sequential_totals == parallel_totals, (
        f"{method_name} produced different results!"
    )

    print(f"{method_name}: Results successfully validated.")


# ============================================================
# 13. PERFORMANCE SUMMARY
# ============================================================

def display_performance_summary(sequential_time, performance_results):
    """
    Displays the performance comparison of all implementations.

    Execution Time:
        Total time required to process all customer orders.

    Speedup:
        Sequential Execution Time / Parallel Execution Time

    Efficiency:
        (Speedup / Number of Workers) * 100

    Sequential efficiency is not applicable because it
    does not use multiple parallel workers.
    """

    print("\n" + "=" * 85)
    print("                 PERFORMANCE COMPARISON")
    print("=" * 85)

    print(
        f"{'Processing Method':<25}"
        f"{'Execution Time':<20}"
        f"{'Speedup':<15}"
        f"{'Efficiency':<15}"
    )

    print("-" * 85)

    # Display sequential performance as the baseline.
    print(
        f"{'Sequential':<25}"
        f"{sequential_time:<20.4f}"
        f"{'1.00x':<15}"
        f"{'N/A':<15}"
    )

    # Store execution times to identify the fastest method.
    all_times = {
        "Sequential": sequential_time
    }

    for method_name, execution_time in performance_results.items():

        # Calculate speedup relative to sequential processing.
        speedup = sequential_time / execution_time

        # Calculate efficiency based on the number of workers.
        efficiency = (speedup / WORKERS) * 100

        print(
            f"{method_name:<25}"
            f"{execution_time:<20.4f}"
            f"{speedup:<15.2f}"
            f"{efficiency:<14.2f}%"
        )

        all_times[method_name] = execution_time

    print("-" * 85)

    # Identify the implementation with the shortest execution time.
    fastest_method = min(all_times, key=all_times.get)

    print(f"\nNumber of Orders: {NUM_ORDERS}")
    print(f"Number of Workers: {WORKERS}")
    print(f"Available CPU Cores: {os.cpu_count() or 1}")

    print(f"\nFastest Processing Method: {fastest_method}")
    print(f"Fastest Execution Time: {all_times[fastest_method]:.4f} seconds")

    print("=" * 85)


# ============================================================
# 14. MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    # Generate the sample customer orders.
    orders = generate_orders()

    print("\nE-COMMERCE ORDER PROCESSING SYSTEM")
    print(f"Total Orders: {NUM_ORDERS}")
    print(f"Available CPU Cores: {os.cpu_count() or 1}")
    print(f"Workers: {WORKERS}")

    # --------------------------------------------------------
    # A. SEQUENTIAL PROCESSING
    # --------------------------------------------------------

    print("\nRunning Sequential Processing...")

    sequential_results, sequential_time = measure_time(
        lambda: sequential_processing(orders)
    )

    print("Sequential Processing Completed.")

    # Display the order details from sequential processing.
    display_orders(sequential_results)

    # --------------------------------------------------------
    # B. MULTITHREADING
    # --------------------------------------------------------

    print("\nRunning Multithreading...")

    threading_results, threading_time = measure_time(
        lambda: multithreading_processing(orders)
    )

    print("Multithreading Completed.")

    # Validate results against sequential processing.
    validate_results(
        sequential_results,
        threading_results,
        "Multithreading"
    )

    # --------------------------------------------------------
    # C. MULTIPROCESSING
    # --------------------------------------------------------

    print("\nRunning Multiprocessing...")

    multiprocessing_results, multiprocessing_time = measure_time(
        lambda: multiprocessing_processing(orders)
    )

    print("Multiprocessing Completed.")

    validate_results(
        sequential_results,
        multiprocessing_results,
        "Multiprocessing"
    )

    # --------------------------------------------------------
    # D. THREADPOOL EXECUTOR
    # --------------------------------------------------------

    print("\nRunning ThreadPoolExecutor...")

    threadpool_results, threadpool_time = measure_time(
        lambda: threadpool_processing(orders)
    )

    print("ThreadPoolExecutor Completed.")

    validate_results(
        sequential_results,
        threadpool_results,
        "ThreadPoolExecutor"
    )

    # --------------------------------------------------------
    # E. PROCESSPOOL EXECUTOR
    # --------------------------------------------------------

    print("\nRunning ProcessPoolExecutor...")

    processpool_results, processpool_time = measure_time(
        lambda: processpool_processing(orders)
    )

    print("ProcessPoolExecutor Completed.")

    validate_results(
        sequential_results,
        processpool_results,
        "ProcessPoolExecutor"
    )

    # --------------------------------------------------------
    # F. DISPLAY PERFORMANCE COMPARISON
    # --------------------------------------------------------

    performance_results = {
        "Multithreading": threading_time,
        "Multiprocessing": multiprocessing_time,
        "ThreadPoolExecutor": threadpool_time,
        "ProcessPoolExecutor": processpool_time
    }

    display_performance_summary(
        sequential_time,
        performance_results
    )

    print("\nAll processing methods have finished successfully!")

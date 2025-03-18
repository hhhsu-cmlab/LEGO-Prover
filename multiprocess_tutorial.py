import multiprocessing

def worker_function(lock, shared_value):
    with lock:
        print(f"Process {multiprocessing.current_process().name} is inside the critical section.")
        shared_value.value += 1
        print(f"Process {multiprocessing.current_process().name} has incremented the value to {shared_value.value}")

if __name__ == '__main__':
    shared_value = multiprocessing.Value('i', 0)
    lock = multiprocessing.Lock()
    processes = []

    for _ in range(3):
        process = multiprocessing.Process(target=worker_function, args=(lock, shared_value))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    print("Final shared value:", shared_value.value)
def find_subarray_with_sum(arr, target_sum):
    current_sum = 0
    start_index = 0
    subarray = []

    for i in range(len(arr)):
        current_sum += arr[i]
        subarray.append(arr[i])

        while current_sum > target_sum:
            current_sum -= arr[start_index]
            subarray.pop(0)
            start_index += 1

        if current_sum == target_sum:
            return subarray

    return None
if __name__ == "__main__":
        arr = list(map(int, input("Enter space-separated values: ").split()))
        sum = int(input("Enter the weight sum "))
        subarray=find_subarray_with_sum(arr, sum)
        print(subarray)
        

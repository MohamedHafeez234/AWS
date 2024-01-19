from collections import Counter

def custom_sort(arr):
    # Count occurrences of each element
    counts = Counter(arr)
    # print (counts)
    # Sort by count and original order
    sorted_arr = sorted(arr, key=lambda x: (-counts[x], arr.index(x)))
    #print (sorted_arr)
    
    result = list(dict.fromkeys(sorted_arr))

    return result

user_input = input("Enter space-separated numbers: ")
A = list(map(int, user_input.split()))
result = custom_sort(A)
print(result)

def subArraySum(arr, n, sum):
        for i in range(0,n):
                currentSum = arr[i]
                if(currentSum == sum):
                        print("Sum found at indexes",i)
                        return
                else:
                        # Try all subarrays starting with 'i'
                        for j in range(i+1,n):
                                currentSum += arr[j]
                                if(currentSum == sum):
                                        for x in range(i,j+1):
                                            print(arr[x],",")
                                        return
        print("No Subarray Found")

if __name__ == "__main__":
        arr = list(map(int, input("Enter space-separated values: ").split()))
        n = len(arr)
        sum = int(input("Enter the weight sum "))
        subArraySum(arr, n, sum)

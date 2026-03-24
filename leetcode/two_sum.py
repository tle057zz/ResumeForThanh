def twoSum(nums: list[int], target: int) -> list[int]:
    first_element = 0
    second_element = 0
    for i in range(len(nums)):
        first_element = nums[i]
        for j in range(i + 1, len(nums)):
            second_element = nums[j]
            if first_element + second_element == target:
                return [i, j]

    return [0, 0]


print(twoSum([2, 7, 11, 15], 9))
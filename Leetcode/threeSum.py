# 给你一个整数数组 nums ，判断是否存在三元组 [nums[i], nums[j], nums[k]] 满足 i != j、i != k 且 j != k ，同时还满足 nums[i] + nums[j] + nums[k] == 0 。请你返回所有和为 0 且不重复的三元组。

# 注意：答案中不可以包含重复的三元组。
# 示例 1：

# 输入：nums = [-1,0,1,2,-1,-4]
# 输出：[[-1,-1,2],[-1,0,1]]
# 解释：
# nums[0] + nums[1] + nums[2] = (-1) + 0 + 1 = 0 。
# nums[1] + nums[2] + nums[4] = 0 + 1 + (-1) = 0 。
# nums[0] + nums[3] + nums[4] = (-1) + 2 + (-1) = 0 。
# 不同的三元组是 [-1,0,1] 和 [-1,-1,2] 。
# 注意，输出的顺序和三元组的顺序并不重要。
# 示例 2：

# 输入：nums = [0,1,1]
# 输出：[]
# 解释：唯一可能的三元组和不为 0 。
# 示例 3：

# 输入：nums = [0,0,0]
# 输出：[[0,0,0]]
# 解释：唯一可能的三元组和为 0 。
 


class Solution(object):
    def threeSum(self, nums):
        """
        :type nums: List[int]
        :rtype: List[List[int]]
        """
        result = []
        #长度小于等于3处理逻辑
        if len(nums) == 3:
            if nums[0] + nums[1] + nums [2] == 0:
                print(nums)
            print("[]")
        #长度大于3处理逻辑
        elif len(nums) > 3:    
            #去重
            set_nums = set(nums)
            list_nums = list(set_nums)
            #排序
            for i in range(0,len(list_nums)):
                for j in range(0,len(list_nums) - i - 1):
                    if list_nums[j] > list_nums[j + 1]:
                        list_nums[j],list_nums[j + 1] = list_nums[j + 1],list_nums[j]

            print(list_nums)
            #查找符合要求
            for i in range(0,len(list_nums)):
                for j in range(0,len(list_nums)):                
                    for k in range(0,len(list_nums)):
                        if i!=j!=k and list_nums[i] + list_nums[j] + list_nums[k] == 0:
                            zero = []
                            zero.append(list_nums[i])
                            zero.append(list_nums[j])
                            zero.append(list_nums[k])
                            result.append(zero)
                            zero.clear()
            print(result)

solution = Solution()
solution.threeSum([1,2,3,9,10,11,0,5,-1,7,7,7,7])
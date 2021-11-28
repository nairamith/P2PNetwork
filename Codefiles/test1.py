super_node_list = [{'supernode': 'c1', 'count': 3, 'purpose': 'D'}, {'supernode': 'c1', 'count': 3, 'purpose': 'F'}]
# purpose_list = [supernode["purpose"] for supernode in super_node_list]
# print(list(set(purpose_list)))

purpose = "F"
count = len(list(filter(lambda node: node["purpose"] == purpose, super_node_list)))
print(count)
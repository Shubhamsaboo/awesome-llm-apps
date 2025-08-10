import numpy as np


class GetData:
    def __init__(self, n_instance: int, n_facilities: int, n_customers: int, max_capacity: int, max_demand: int, max_cost: int):
        """
        Initialize the GetDataCFLP class for the Capacitated Facility Location Problem.

        Args:
            n_instance: Number of instances to generate.
            n_facilities: Number of facilities.
            n_customers: Number of customers.
            max_capacity: Maximum capacity of any facility.
            max_demand: Maximum demand of any customer.
            max_cost: Maximum cost for assigning a customer to a facility.
        """
        self.n_instance = n_instance
        self.n_facilities = n_facilities
        self.n_customers = n_customers
        self.max_capacity = max_capacity
        self.max_demand = max_demand
        self.max_cost = max_cost

    def generate_instances(self):
        """
        Generate instances for the Capacitated Facility Location Problem.

        Returns:
            A list of dictionaries, where each dictionary contains:
            - facility_capacities: A list of capacities for each facility.
            - customer_demands: A list of demands for each customer.
            - assignment_costs: A 2D list (matrix) of costs, where the cost of assigning
              customer j to facility i is assignment_costs[i][j].
        """
        np.random.seed(2024)  # Set seed for reproducibility
        instance_data = []

        for _ in range(self.n_instance):
            # Generate random capacities for facilities
            facility_capacities = np.random.randint(5, self.max_capacity + 1, size=self.n_facilities).tolist()

            # Generate random demands for customers
            customer_demands = np.random.randint(5, self.max_demand + 1, size=self.n_customers).tolist()

            # Generate random assignment costs (facility-to-customer cost matrix)
            assignment_costs = np.random.randint(5, self.max_cost + 1, size=(self.n_facilities, self.n_customers)).tolist()

            instance_data.append({
                "facility_capacities": facility_capacities,
                "customer_demands": customer_demands,
                "assignment_costs": assignment_costs
            })

        return instance_data

# # Example usage:
# data_generator = GetDataCFLP(n_instance=3, n_facilities=5, n_customers=8, max_capacity=100, max_demand=20, max_cost=50)
# instances = data_generator.generate_instances()
# for instance in instances:
#     print("Facility Capacities:", instance["facility_capacities"])
#     print("Customer Demands:", instance["customer_demands"])
#     print("Assignment Costs:")
#     for row in instance["assignment_costs"]:
#         print(row)
#     print()

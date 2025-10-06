#include <iostream>
#include <iomanip>
#include <vector>
#include <chrono>
#include <limits>

// Linear Congruential Generator
long long lcg(long long seed, int a = 1664525, int c = 1013904223, long long m = 1LL << 32) {
    return (a * seed + c) % m;
}

// Maximum subarray sum using the LCG-based number generator
long long max_subarray_sum(int n, long long seed, int min_val, int max_val) {
    std::vector<int> random_numbers(n);
    long long a = 1664525, c = 1013904223, m = 1LL << 32;
    long long value = seed;
    
    for (int i = 0; i < n; ++i) {
        value = (a * value + c) % m;
        random_numbers[i] = value % (max_val - min_val + 1) + min_val;
    }
    
    long long max_sum = std::numeric_limits<long long>::min();
    for (int i = 0; i < n; ++i) {
        long long current_sum = 0;
        for (int j = i; j < n; ++j) {
            current_sum += random_numbers[j];
            if (current_sum > max_sum) {
                max_sum = current_sum;
            }
        }
    }
    return max_sum;
}

// Calculate total max subarray sum over 20 LCG-generated sequences
long long total_max_subarray_sum(int n, long long initial_seed, int min_val, int max_val) {
    long long total_sum = 0;
    long long seed = initial_seed;
    for (int i = 0; i < 20; ++i) {
        seed = lcg(seed);
        total_sum += max_subarray_sum(n, seed, min_val, max_val);
    }
    return total_sum;
}

int main() {
    // Parameters
    int n = 10000; // Number of random numbers
    long long initial_seed = 42; // Initial seed for the LCG
    int min_val = -10; // Minimum value of random numbers
    int max_val = 10; // Maximum value of random numbers

    // Timing the function
    auto start_time = std::chrono::high_resolution_clock::now();
    long long result = total_max_subarray_sum(n, initial_seed, min_val, max_val);
    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end_time - start_time;

    // Output result and execution time
    std::cout << "Total Maximum Subarray Sum (20 runs): " << result << std::endl;
    std::cout << std::fixed << std::setprecision(6) 
              << "Execution Time: " << elapsed.count() << " seconds" << std::endl;

    return 0;
}

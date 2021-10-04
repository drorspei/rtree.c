#include <vector>
#include <stdint.h>
#include <cstdlib>
#include <algorithm>
#include "rtree.h"

bool batch_iter(const double* rect, const void* item, void* udata) {
    std::vector<int>* values = (std::vector<int>*)(udata);
    int i = *(int64_t*)item;
    values->push_back(i);
    return true;
}

extern "C" {
    bool rtree_search_batch(
        rtree* r,
        size_t dimension,
        double* mins_maxs,
        int64_t size,
        int32_t** out_offsets,
        int64_t** out_values,
        int64_t* out_size
    ) {     
        std::vector<int> offsets;
        std::vector<int> values;

        for (size_t i = 0; i < size; i++)
        {
            offsets.push_back(values.size());
            if (!rtree_search(
                r,
                &mins_maxs[2 * dimension * i],
                batch_iter,
                (void*)&values
            )) {
                return false;
            }
        }

        offsets.push_back(values.size());
        
        *out_size = offsets.size();

        int32_t msize = sizeof(int32_t) * offsets.size();
        msize = 64 * ((msize + 63) / 64);
        *out_offsets = (int32_t*)malloc(msize);

        if (!*out_offsets) {
            return false;
        }

        std::copy(
            offsets.data(),
            offsets.data() + offsets.size(),
            *out_offsets
        );

        msize = sizeof(int64_t) * values.size();
        msize = 64 * ((msize + 63) / 64);
        *out_values = (int64_t*)malloc(msize);
        
        if (!*out_values) {
            free(*out_offsets);
            return false;
        }

        std::copy(
            values.data(),
            values.data() + values.size(),
            *out_values
        );

        return true;
    }
}

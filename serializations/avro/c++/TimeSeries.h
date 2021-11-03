/*
 *
 * Copyright 2021 COVESA
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 */

#include "err.h"
#include "value.h"
#include <string>
#include <vector>

class TimeSeries {
    //content

   std::string signal_identifier;
   unsigned int count;
   std::vector<Value_t> items;

   public:
    TimeSeries(std::string s) : signal_identifier(s) {}
    TimeSeries(std::string s, unsigned int c, std::vector<Value_t> i) : signal_identifier(s), count(c), items(i) 
    {
       count = items.size();
    }

    // Serialize the data using AVRO
    err_t encode();
    err_t decode();
};

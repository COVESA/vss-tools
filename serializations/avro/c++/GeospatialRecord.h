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

#include <tuple>
#include "err.h"
#include "value.h"
#include "err.h"

class GeospatialRecord {
    typedef std::tuple<int,int> GNSSposition_t;

    GNSSposition_t pos;
    long int ts;
    Value_t value;

   public:
    GeospatialRecord(GNSSposition_t p, long int t, Value_t v)
        : pos(p), ts(t) {
        value = v;
    }
    // Serialize the data using AVRO
    err_t encode();
    err_t decode();
};

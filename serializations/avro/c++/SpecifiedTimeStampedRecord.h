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

class SpecifiedTimeStampedRecord {
    //content
   public:
    SpecifiedTimeStampedRecord();
 
    // Serialize the data using AVRO
    err_t encode();
    err_t decode();
};

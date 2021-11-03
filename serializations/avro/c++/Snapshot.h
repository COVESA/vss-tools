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

#include <vector>
#include "err.h"
#include "SpecifiedTimeStampedRecord.h"

typedef long time_t;

typedef struct {
   time_t start;
   time_t end;
} duration_t;

typedef std::vector<SpecifiedTimeStampedRecord> SpecifiedItems_t;

class Snapshot {
   //content

   int count;
   duration_t timeperiod;
   SpecifiedItems_t items;

   public:
   Snapshot();
   Snapshot(duration_t t, SpecifiedItems_t i) : timeperiod(t), items(i)
   {
      count = items.size();
   }
   Snapshot(time_t t, SpecifiedItems_t i) : items(i) 
   {
      duration_t d = { t, t } ;  //  Assuming start == end here
      Snapshot(d, i); // Call other constructor
   }

   // Serialize the data using AVRO
   err_t encode();
   err_t decode();
};

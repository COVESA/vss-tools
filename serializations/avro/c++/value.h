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

#include <string>
#include <vector>

typedef union value_u {
   int _int;
   long _long;
   float _float;
   double _double;
   // ... mor
} Value_t; 

typedef std::vector<Value_t> VSS_Array_t;

#! /usr/bin/env python

# Copyright 2014 Tom SF Haines

# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.



import frf

import os
import numpy



# A toy minion classifier, for optimising the employment of your evil army.



categories = ('minion_muscle', 'minion_scientist', 'competition', 'guinea_pig', 'victim')

train_count = {'minion_muscle':32, 'minion_scientist':32, 'competition':32, 'guinea_pig':32, 'victim':256}



class Eyesight:
  cont = False
  
  Glasses = 0
  TwentyTwenty = 1
  WompRat = 2

  dist = {'minion_muscle':(0.0,0.4,0.6), 'minion_scientist':(0.5,0.3,0.2), 'competition':(0.1,0.2,0.7), 'guinea_pig':(0.4,0.4,0.2), 'victim':(0.5,0.3,0.2)}


class MindSet:
  cont = False
  
  Philosopher = 0
  Intelectual = 1
  Religious = 2
  Thoughtless = 3

  dist = {'minion_muscle':(0.0,0.0,0.5,0.5), 'minion_scientist':(0.5,0.5,0.0,0.0), 'competition':(0.6,0.2,0.2,0.0), 'guinea_pig':(0.0,0.0,0.6,0.4), 'victim':(0.1,0.2,0.3,0.4)}


class Body:
  cont = True
  
  Muscle = 0
  Height = 1
  Width = 2

  length = 3

  mean = {'minion_muscle':(1.0,2.0,0.6), 'minion_scientist':(0.1,1.6,0.3), 'competition':(1.0,2.4,0.2), 'guinea_pig':(0.5,1.3,0.4), 'victim':(0.5,1.8,0.4)}
  
  covar = {'minion_muscle':((0.1,0.2,0.2),(0.2,0.2,-0.3),(0.2,-0.3,0.8)), 'minion_scientist':((0.4,0.0,0.0),(0.0,0.4,-0.2),(0.0,-0.2,0.4)), 'competition':((0.1,0.0,0.0),(0.0,0.1,0.0),(0.0,0.0,0.1)), 'guinea_pig':((0.4,0.1,0.1),(0.1,0.4,-0.2),(0.1,-0.2,0.4)), 'victim':((0.4,0.2,0.2),(0.2,0.5,-0.3),(0.2,-0.3,0.5))}


class Brains:
  cont = True
  
  Intellect = 0
  Bravery = 1
  Submissive = 2

  length = 3

  mean = {'minion_muscle':(0.1,0.8,1.0), 'minion_scientist':(1.0,0.0,0.7), 'competition':(1.0,1.0,0.0), 'guinea_pig':(0.1,0.1,1.0), 'victim':(0.1,0.1,0.1)}

  covar = {'minion_muscle':((0.2,-0.2,-0.5),(-0.2,0.1,0.0),(-0.5,0.0,0.5)), 'minion_scientist':((0.3,0.0,-0.4),(0.0,0.1,0.0),(-0.4,0.0,0.4)), 'competition':((0.1,0.0,0.0),(0.0,0.1,0.0),(0.0,0.0,0.1)), 'guinea_pig':((0.3,-0.2,-0.5),(-0.2,0.3,0.0),(-0.5,0.0,0.6)), 'victim':((0.3,-0.2,-0.2),(-0.2,0.3,0.0),(-0.2,0.0,0.3))}


  
attributes = (Eyesight, MindSet, Body, Brains)
int_length = len(filter(lambda a: a.cont==False, attributes))
real_length = sum(map(lambda a: a.length if a.cont else 0, attributes))



# Function that can be given an entry from categories and returns an instance, as a tuple of (int vector, real vector)...
def generate(cat):
  int_ret = numpy.empty(int_length, dtype=numpy.int32)
  real_ret = numpy.empty(real_length, dtype=numpy.float32)
  int_offset = 0
  real_offset = 0

  for att in attributes:
    if att.cont:
      real_ret[real_offset:real_offset+att.length] = numpy.random.multivariate_normal(att.mean[cat], att.covar[cat])
      real_offset += att.length
    else:
      int_ret[int_offset] = numpy.nonzero(numpy.random.multinomial(1,att.dist[cat]))[0][0]
      int_offset += 1

  return (int_ret, real_ret)



# Generate the trainning data...
length = sum(train_count.itervalues())
int_dm = numpy.empty((length, int_length), dtype=numpy.int32)
real_dm = numpy.empty((length, real_length), dtype=numpy.float32)
cats = numpy.empty(length, dtype=numpy.int32)

pos = 0
for cat in categories:
  cat_ind = categories.index(cat)
  for _ in xrange(train_count[cat]):
    int_dm[pos,:], real_dm[pos,:] = generate(cat)
    cats[pos] = cat_ind
    pos += 1

    
    
# Train a forest...
forest = frf.Forest()
forest.configure('C', 'C', 'O'*int_length + 'S'*real_length)
forest.min_exemplars = 2

oob = forest.train((int_dm, real_dm), cats, 6)

print 'Made forest:'
for i in xrange(len(forest)):
  if oob!=None:
    extra = ', oob = %s' % str(oob[i,:])
  else:
    extra = ''
    
  print '  Tree %i: %i bytes, %i nodes%s' % (i, forest[i].size, forest[i].nodes(), extra)
print



# Save it to disk and reload it, to check that functionality works...
frf.save_forest('temp.rf', forest)
del forest

print 'Saved to disk size = %i bytes' % os.path.getsize('temp.rf')
print

forest = frf.load_forest('temp.rf')
os.remove('temp.rf')



# Test...
print 'Testing:'
for cat in categories:
  # Generate exemplars...
  int_dm = numpy.empty((256, int_length), dtype=numpy.int32)
  real_dm = numpy.empty((int_dm.shape[0], real_length), dtype=numpy.float32)
  for i in xrange(int_dm.shape[0]):
    int_dm[i,:], real_dm[i,:] = generate(cat)
  
  # Test them...
  res = forest.predict((int_dm, real_dm))[0]
  correct = (numpy.argmax(res['prob'], axis=1)==categories.index(cat)).sum()
  
  # Output results...
  print '  Of %i %s %i (%.1f%%) were correctly detected.'%(int_dm.shape[0], cat.replace('_', ' '), correct, 100.0*correct/float(int_dm.shape[0]))
